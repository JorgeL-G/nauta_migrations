"""
Interfaz de línea de comandos para gestionar migraciones
"""
import click
from pathlib import Path
from nauta_migrations.migrate import MigrationManager
from nauta_migrations.config import config


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Sistema de gestión de migraciones para MongoDB"""
    pass


@cli.command()
@click.argument("description")
@click.option("--migrations-dir", default=None, help="Directorio de migraciones")
def create(description: str, migrations_dir: str):
    """Crear una nueva migración"""
    manager = MigrationManager()
    if migrations_dir:
        manager.migrations_dir = Path(migrations_dir)
        manager.migrations_dir.mkdir(exist_ok=True)
    
    try:
        filepath = manager.create_migration(description)
        click.echo(f"✓ Migración creada: {filepath}")
        click.echo(f"  Edita el archivo para implementar upgrade() y downgrade()")
    except Exception as e:
        click.echo(f"✗ Error creando migración: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option("--mongodb-url", default=None, help="URL de conexión a MongoDB")
@click.option("--database", default=None, help="Nombre de la base de datos")
@click.option("--migrations-dir", default=None, help="Directorio de migraciones")
def migrate(mongodb_url: str, database: str, migrations_dir: str):
    """Ejecutar migraciones pendientes"""
    manager = MigrationManager(
        mongodb_url=mongodb_url or config.get_mongodb_url(),
        database=database or config.get_mongodb_database()
    )
    
    if migrations_dir:
        manager.migrations_dir = Path(migrations_dir)
    
    try:
        manager.connect()
        pending = manager.get_pending_migrations()
        
        if not pending:
            click.echo("No hay migraciones pendientes")
            return
        
        click.echo(f"Migraciones pendientes: {len(pending)}")
        
        for migration_file in pending:
            click.echo(f"  → Aplicando {migration_file.name}...", nl=False)
            if manager.apply_migration(migration_file):
                click.echo(" ✓")
            else:
                click.echo(" ✗")
                raise click.Abort()
        
        click.echo(f"\n✓ Todas las migraciones aplicadas correctamente")
    except Exception as e:
        click.echo(f"\n✗ Error ejecutando migraciones: {e}", err=True)
        raise click.Abort()
    finally:
        manager.disconnect()


@cli.command()
@click.option("--migration", default=None, help="Nombre de la migración a revertir (opcional)")
@click.option("--mongodb-url", default=None, help="URL de conexión a MongoDB")
@click.option("--database", default=None, help="Nombre de la base de datos")
@click.option("--migrations-dir", default=None, help="Directorio de migraciones")
@click.confirmation_option(prompt="¿Estás seguro de que quieres revertir la migración?")
def rollback(migration: str, mongodb_url: str, database: str, migrations_dir: str):
    """Revertir una migración"""
    manager = MigrationManager(
        mongodb_url=mongodb_url or config.get_mongodb_url(),
        database=database or config.get_mongodb_database()
    )
    
    if migrations_dir:
        manager.migrations_dir = Path(migrations_dir)
    
    try:
        manager.connect()
        
        migration_name = migration
        if migration_name:
            click.echo(f"Revirtiendo migración: {migration_name}")
        else:
            click.echo("Revirtiendo última migración...")
        
        if manager.rollback_migration(migration_name):
            click.echo("✓ Migración revertida correctamente")
        else:
            click.echo("✗ Error revirtiendo migración", err=True)
            raise click.Abort()
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()
    finally:
        manager.disconnect()


@cli.command()
@click.option("--mongodb-url", default=None, help="URL de conexión a MongoDB")
@click.option("--database", default=None, help="Nombre de la base de datos")
@click.option("--migrations-dir", default=None, help="Directorio de migraciones")
def status(mongodb_url: str, database: str, migrations_dir: str):
    """Mostrar estado de las migraciones"""
    manager = MigrationManager(
        mongodb_url=mongodb_url or config.get_mongodb_url(),
        database=database or config.get_mongodb_database()
    )
    
    if migrations_dir:
        manager.migrations_dir = Path(migrations_dir)
    
    try:
        manager.connect()
        status_info = manager.get_status()
        
        click.echo("\nEstado de Migraciones")
        click.echo("=" * 50)
        click.echo(f"Total: {status_info['total']}")
        click.echo(f"Aplicadas: {status_info['applied']}")
        click.echo(f"Pendientes: {status_info['pending']}")
        
        if status_info['applied_migrations']:
            click.echo("\nMigraciones Aplicadas:")
            for m in status_info['applied_migrations']:
                applied_at = m.get('applied_at', '').strftime('%Y-%m-%d %H:%M:%S') if m.get('applied_at') else 'N/A'
                click.echo(f"  ✓ {m['name']} - {applied_at}")
        
        if status_info['pending_migrations']:
            click.echo("\nMigraciones Pendientes:")
            for name in status_info['pending_migrations']:
                click.echo(f"  ○ {name}")
        
        click.echo()
    except Exception as e:
        click.echo(f"✗ Error obteniendo estado: {e}", err=True)
        raise click.Abort()
    finally:
        manager.disconnect()


@cli.command()
@click.option("--migrations-dir", default=None, help="Directorio de migraciones")
def list(migrations_dir: str):
    """Listar todas las migraciones"""
    manager = MigrationManager()
    
    if migrations_dir:
        manager.migrations_dir = Path(migrations_dir)
    
    try:
        manager.connect()
        all_migrations = manager.get_migration_files()
        applied = {m["name"] for m in manager.get_applied_migrations()}
        
        if not all_migrations:
            click.echo("No hay migraciones definidas")
            return
        
        click.echo("\nMigraciones Disponibles")
        click.echo("=" * 50)
        
        for migration_file in all_migrations:
            status = "✓ Aplicada" if migration_file.name in applied else "○ Pendiente"
            click.echo(f"  {status} - {migration_file.name}")
        
        click.echo()
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()
    finally:
        manager.disconnect()


def main():
    """Punto de entrada principal"""
    cli()


if __name__ == "__main__":
    main()

