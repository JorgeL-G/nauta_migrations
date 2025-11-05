# Nauta Migrations

Sistema de gestión de migraciones para MongoDB usando Python y pymongo.

## Características

- ✅ Crear nuevas migraciones con plantilla
- ✅ Ejecutar migraciones pendientes
- ✅ Revertir migraciones (rollback)
- ✅ Consultar estado de migraciones
- ✅ Listar todas las migraciones
- ✅ Seguimiento de versiones en la base de datos
- ✅ Validación de esquema con $jsonSchema
- ✅ Soporte para campos datetime

## Instalación

### Requisitos

- Python 3.8 o superior (recomendado 3.10)
- MongoDB
- Anaconda o Miniconda (opcional, pero recomendado)

### Instalación con Anaconda (Recomendado)

1. Clonar o descargar el proyecto:
```bash
cd nauta_migrations
```

2. Crear y activar el entorno virtual con conda:
```bash
# Crear el entorno desde el archivo environment.yml
conda env create -f environment.yml

# Activar el entorno
conda activate nauta_migrations
```

3. Instalar el paquete en modo desarrollo:
```bash
pip install -e .
```

4. Configurar variables de entorno:
```bash
cp .env.example .env
```

### Instalación sin Anaconda

1. Clonar o descargar el proyecto:
```bash
cd nauta_migrations
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Instalar el paquete en modo desarrollo:
```bash
pip install -e .
```

4. Configurar variables de entorno:
```bash
cp .env.example .env
```

Editar el archivo `.env` con tus configuraciones:
```env
MONGODB_URL=mongodb://localhost:27017/nauta_db
MONGODB_DATABASE=nauta_db
MIGRATIONS_DIR=migrations
```

## Uso

### Comandos Disponibles

#### Crear una nueva migración

```bash
nauta-migrate create "descripción de la migración"
```

Esto creará un archivo en el directorio `migrations/` con el formato `YYYYMMDDHHMMSS_descripcion.py`.

#### Ejecutar migraciones pendientes

```bash
nauta-migrate migrate
```

Aplica todas las migraciones pendientes en orden cronológico.

#### Revertir una migración

```bash
# Revertir la última migración
nauta-migrate rollback

# Revertir una migración específica
nauta-migrate rollback --migration 20231104120000_agregar_campo.py
```

#### Consultar estado

```bash
nauta-migrate status
```

Muestra el estado de todas las migraciones: totales, aplicadas y pendientes.

#### Listar migraciones

```bash
nauta-migrate list
```

Lista todas las migraciones disponibles y su estado.

## Formato de Migraciones

Las migraciones son archivos Python que contienen una clase `Migration` que hereda de `BaseMigration`. Cada migración debe implementar:

- `upgrade()`: Método para aplicar los cambios
- `downgrade()`: Método para revertir los cambios

### Ejemplo de Migración

#### Ejemplo básico: Agregar campo

```python
"""
Migration: Add email field to users
Created: 2023-11-04 12:00:00
"""

from nauta_migrations.migrate import BaseMigration


class Migration(BaseMigration):
    """Add email field to users"""
    
    def upgrade(self):
        """
        Apply changes to the database.
        Access the database using self.db
        """
        # Add email field with default value
        self.db.usuarios.update_many(
            {},
            {"$set": {"email": ""}}
        )
    
    def downgrade(self):
        """
        Revert changes applied in upgrade().
        """
        # Remove email field
        self.db.usuarios.update_many(
            {},
            {"$unset": {"email": ""}}
        )
```

#### Ejemplo avanzado: Crear colección con validación de esquema

```python
"""
Migration: create_collection_transactions
Created: 2025-11-04 15:56:56

Creates the 'transactions' collection with schema validations:
- Amount: Decimal, required, greater than 0
- Currency: Enum (USD, EUR, MXN, etc.), required
- Transaction date: required, datetime type
- Category: String, optional
- created_at: automatic datetime
"""

from nauta_migrations.migrate import BaseMigration


class Migration(BaseMigration):
    """Create transactions collection with validations"""
    
    def upgrade(self):
        """
        Create the 'transactions' collection with schema validation.
        """
        collection_name = "transactions"
        
        # Schema validation using $jsonSchema
        validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["monto", "moneda", "fecha_transaccion", "created_at"],
                "properties": {
                    "monto": {
                        "bsonType": "decimal",
                        "description": "Transaction amount (required, must be greater than 0)",
                        "minimum": 0
                    },
                    "moneda": {
                        "enum": ["USD", "EUR", "MXN", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "BRL"],
                        "description": "Transaction currency (required)",
                    },
                    "fecha_transaccion": {
                        "bsonType": "date",
                        "description": "Transaction date (required, datetime type)"
                    },
                    "created_at": {
                        "bsonType": "date",
                        "description": "Document creation date and time - datetime (required)"
                    }
                }
            }
        }
        
        # Create collection with validation
        if collection_name in self.db.list_collection_names():
            print(f"Collection '{collection_name}' already exists. Skipping creation.")
            return
        
        self.db.create_collection(
            collection_name,
            validator=validator,
            validationLevel="strict",
            validationAction="error"
        )
        
        print(f"✓ Collection '{collection_name}' created successfully with validations")
    
    def downgrade(self):
        """
        Drop the 'transactions' collection.
        """
        collection_name = "transactions"
        
        if collection_name in self.db.list_collection_names():
            self.db.drop_collection(collection_name)
            print(f"✓ Collection '{collection_name}' dropped successfully")
```

## Estructura del Proyecto

```
nauta_migrations/
├── migrations/              # Directorio de migraciones
│   └── YYYYMMDDHHMMSS_*.py
├── nauta_migrations/        # Módulo principal
│   ├── __init__.py
│   ├── cli.py              # Interfaz de línea de comandos
│   ├── config.py           # Configuración
│   └── migrate.py          # Lógica de migraciones
├── .env                    # Variables de entorno (no versionar)
├── .env.example            # Plantilla de variables de entorno
├── requirements.txt        # Dependencias
├── setup.py               # Configuración del paquete
└── README.md              # Este archivo
```

## Seguimiento de Versiones

El sistema registra las migraciones aplicadas en una colección `_migrations` en la base de datos MongoDB. Cada registro contiene:

- `version`: Identificador de la migración
- `name`: Nombre del archivo
- `description`: Descripción de la migración
- `applied_at`: Fecha y hora de aplicación

## Opciones de Línea de Comandos

Todos los comandos aceptan opciones para sobrescribir la configuración:

- `--mongodb-url`: URL de conexión a MongoDB
- `--database`: Nombre de la base de datos
- `--migrations-dir`: Directorio de migraciones

Ejemplo:
```bash
nauta-migrate migrate --mongodb-url mongodb://localhost:27017/otra_db --database otra_db
```

## Notas Técnicas

### Validación de Esquema

El sistema soporta validación de esquema usando `$jsonSchema` de MongoDB. Esto permite definir reglas de validación estrictas para las colecciones.

### Tipos de Datos

- **decimal**: Para valores monetarios (precisión exacta)
- **date**: Para campos de fecha y hora (datetime)
- **string**: Para texto
- **enum**: Para valores predefinidos

### Verificación de Objetos Database

Los objetos `Database` de PyMongo no pueden ser evaluados directamente en condiciones booleanas. Use `if self.db is None:` en lugar de `if not self.db:`.

## Desarrollo

### Ejecutar comandos sin instalar

```bash
python -m nauta_migrations.cli create "descripción"
```

## Licencia

Este proyecto es de uso interno.

## Soporte

Para problemas o preguntas, contactar al equipo de desarrollo.

