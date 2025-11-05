"""
Módulo de lógica de migraciones
"""
import importlib.util
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from pymongo import MongoClient
from pymongo.database import Database

from nauta_migrations.config import config


class BaseMigration:
    """Clase base para las migraciones"""
    
    def __init__(self):
        self.db: Optional[Database] = None
    
    def upgrade(self):
        """
        Método para aplicar cambios a la base de datos.
        Debe ser implementado por las clases hijas.
        """
        raise NotImplementedError("El método upgrade() debe ser implementado")
    
    def downgrade(self):
        """
        Método para revertir cambios aplicados en upgrade().
        Debe ser implementado por las clases hijas.
        """
        raise NotImplementedError("El método downgrade() debe ser implementado")


class MigrationManager:
    """Gestor de migraciones"""
    
    def __init__(self, mongodb_url: Optional[str] = None, database: Optional[str] = None):
        self.mongodb_url = mongodb_url or config.get_mongodb_url()
        self.database_name = database or config.get_mongodb_database()
        self.migrations_dir = config.get_migrations_dir()
        self.client = None
        self.db = None
    
    def connect(self):
        """Conectar a MongoDB"""
        self.client = MongoClient(self.mongodb_url)
        self.db = self.client[self.database_name]
    
    def disconnect(self):
        """Desconectar de MongoDB"""
        if self.client:
            self.client.close()
    
    def get_migrations_collection(self):
        """Obtener la colección de seguimiento de migraciones"""
        if self.db is None:
            self.connect()
        return self.db["_migrations"]
    
    def get_migration_files(self) -> List[Path]:
        """Obtener lista de archivos de migración ordenados"""
        if not self.migrations_dir.exists():
            return []
        
        migration_files = [
            f for f in self.migrations_dir.iterdir()
            if f.is_file() and f.suffix == ".py" and not f.name.startswith("__")
        ]
        
        # Ordenar por nombre (que incluye timestamp)
        migration_files.sort(key=lambda x: x.name)
        return migration_files
    
    def get_applied_migrations(self) -> List[Dict[str, Any]]:
        """Obtener lista de migraciones ya aplicadas"""
        collection = self.get_migrations_collection()
        return list(collection.find().sort("applied_at", 1))
    
    def get_pending_migrations(self) -> List[Path]:
        """Obtener lista de migraciones pendientes"""
        applied = {m["name"] for m in self.get_applied_migrations()}
        all_migrations = self.get_migration_files()
        return [m for m in all_migrations if m.name not in applied]
    
    def create_migration(self, description: str) -> Path:
        """Crear un nuevo archivo de migración"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        # Limpiar descripción para nombre de archivo
        safe_description = description.lower().replace(" ", "_").replace("-", "_")
        safe_description = "".join(c for c in safe_description if c.isalnum() or c == "_")
        
        filename = f"{timestamp}_{safe_description}.py"
        filepath = self.migrations_dir / filename
        
        template = f'''"""
Migración: {description}
Creada: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

from nauta_migrations.migrate import BaseMigration


class Migration(BaseMigration):
    """{description}"""
    
    def upgrade(self):
        """
        Aplicar cambios a la base de datos.
        Accede a la base de datos mediante self.db
        Ejemplo:
            self.db.collection_name.update_many({{}}, {{"$set": {{"campo": "valor"}}}})
        """
        # TODO: Implementar lógica de migración
        pass
    
    def downgrade(self):
        """
        Revertir cambios aplicados en upgrade().
        Ejemplo:
            self.db.collection_name.update_many({{}}, {{"$unset": {{"campo": ""}}}})
        """
        # TODO: Implementar lógica de reversión
        pass
'''
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(template)
        
        return filepath
    
    def load_migration(self, filepath: Path) -> Optional[BaseMigration]:
        """Cargar una clase de migración desde un archivo"""
        try:
            # Cargar el módulo desde el archivo
            spec = importlib.util.spec_from_file_location(filepath.stem, filepath)
            if spec is None or spec.loader is None:
                print(f"Error: No se pudo cargar el módulo {filepath.name}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            
            # Inyectar db en el módulo antes de ejecutar
            module.db = self.db
            
            # Ejecutar el módulo
            spec.loader.exec_module(module)
            
            # Obtener la clase Migration
            if not hasattr(module, "Migration"):
                print(f"Error: La migración {filepath.name} no contiene una clase 'Migration'")
                return None
            
            migration_class = module.Migration
            
            # Crear instancia con acceso a la base de datos
            migration = migration_class()
            migration.db = self.db
            
            return migration
        except Exception as e:
            print(f"Error cargando migración {filepath.name}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def apply_migration(self, filepath: Path) -> bool:
        """Aplicar una migración"""
        try:
            if self.db is None:
                self.connect()
            
            migration = self.load_migration(filepath)
            if not migration:
                return False
            
            # Ejecutar upgrade
            migration.upgrade()
            
            # Registrar en la colección de migraciones
            collection = self.get_migrations_collection()
            collection.insert_one({
                "version": filepath.stem,
                "name": filepath.name,
                "description": filepath.stem.split("_", 1)[1] if "_" in filepath.stem else "",
                "applied_at": datetime.now()
            })
            
            return True
        except Exception as e:
            print(f"Error aplicando migración {filepath.name}: {e}")
            return False
    
    def rollback_migration(self, migration_name: Optional[str] = None) -> bool:
        """Revertir una migración"""
        try:
            if self.db is None:
                self.connect()
            
            applied = self.get_applied_migrations()
            if not applied:
                print("No hay migraciones aplicadas para revertir")
                return False
            
            # Si no se especifica, revertir la última
            if not migration_name:
                migration_record = applied[-1]
            else:
                migration_record = next(
                    (m for m in applied if m["name"] == migration_name),
                    None
                )
                if not migration_record:
                    print(f"Migración {migration_name} no encontrada")
                    return False
            
            # Cargar y ejecutar downgrade
            filepath = self.migrations_dir / migration_record["name"]
            migration = self.load_migration(filepath)
            if not migration:
                return False
            
            migration.downgrade()
            
            # Eliminar registro
            collection = self.get_migrations_collection()
            collection.delete_one({"_id": migration_record["_id"]})
            
            return True
        except Exception as e:
            print(f"Error revirtiendo migración: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado de las migraciones"""
        all_migrations = self.get_migration_files()
        applied = self.get_applied_migrations()
        applied_names = {m["name"] for m in applied}
        pending = [m for m in all_migrations if m.name not in applied_names]
        
        return {
            "total": len(all_migrations),
            "applied": len(applied),
            "pending": len(pending),
            "applied_migrations": applied,
            "pending_migrations": [m.name for m in pending]
        }

