"""
Módulo de configuración para gestionar la conexión a MongoDB
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

# Cargar variables de entorno desde .env
load_dotenv()


class Config:
    """Configuración de la aplicación"""
    
    def __init__(self):
        self.mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017/nauta_db")
        self.mongodb_database = os.getenv("MONGODB_DATABASE", None)
        self.migrations_dir = os.getenv("MIGRATIONS_DIR", "migrations")
        
        # Si no se especifica base de datos en variable separada, intentar extraerla de la URL
        if not self.mongodb_database:
            # Extraer nombre de base de datos de la URL si está presente
            if "/" in self.mongodb_url:
                url_parts = self.mongodb_url.rsplit("/", 1)
                if len(url_parts) > 1 and url_parts[1] and "?" not in url_parts[1]:
                    self.mongodb_database = url_parts[1]
                else:
                    self.mongodb_database = "nauta_db"
            else:
                self.mongodb_database = "nauta_db"
        
        # Convertir a Path para mejor manejo
        self.migrations_path = Path(self.migrations_dir)
        
        # Asegurar que el directorio de migraciones existe
        self.migrations_path.mkdir(exist_ok=True)
    
    def get_mongodb_url(self) -> str:
        """Obtener la URL de conexión a MongoDB"""
        return self.mongodb_url
    
    def get_mongodb_database(self) -> str:
        """Obtener el nombre de la base de datos"""
        return self.mongodb_database
    
    def get_migrations_dir(self) -> Path:
        """Obtener el directorio de migraciones"""
        return self.migrations_path
    
    @classmethod
    def from_env(cls) -> "Config":
        """Crear configuración desde variables de entorno"""
        return cls()


# Instancia global de configuración
config = Config.from_env()

