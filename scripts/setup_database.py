#!/usr/bin/env python3
"""
Setup database schema and initial data
"""

import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.config.settings import settings
from src.models.database import Base, init_models
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def create_database():
    """Create database if it doesn't exist"""
    # Connect to PostgreSQL without database
    engine = create_engine(
        f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/postgres"
    )
    
    conn = engine.connect()
    conn.execute(text("commit"))  # Close any transaction
    
    # Check if database exists
    exists = conn.execute(
        text(f"SELECT 1 FROM pg_database WHERE datname = '{settings.db_name}'")
    ).fetchone()
    
    if not exists:
        conn.execute(text(f"CREATE DATABASE {settings.db_name}"))
        logger.info(f"Created database: {settings.db_name}")
    else:
        logger.info(f"Database already exists: {settings.db_name}")
    
    conn.close()
    engine.dispose()


def create_tables():
    """Create all tables"""
    # Initialize models
    init_models()
    
    # Create engine with database
    engine = create_engine(settings.database_url)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Created all database tables")
    
    return engine


def create_extensions(engine):
    """Create PostgreSQL extensions"""
    with engine.connect() as conn:
        # Create useful extensions
        extensions = ['uuid-ossp', 'pg_stat_statements', 'pg_trgm']
        
        for ext in extensions:
            try:
                conn.execute(text(f"CREATE EXTENSION IF NOT EXISTS \"{ext}\""))
                logger.info(f"Created extension: {ext}")
            except Exception as e:
                logger.warning(f"Could not create extension {ext}: {e}")
        
        conn.commit()


def create_indexes(engine):
    """Create additional indexes for performance"""
    indexes = [
        # Transacciones
        "CREATE INDEX IF NOT EXISTS idx_transacciones_fecha ON transacciones_ventas(fecha_hora)",
        "CREATE INDEX IF NOT EXISTS idx_transacciones_cliente ON transacciones_ventas(id_cliente)",
        "CREATE INDEX IF NOT EXISTS idx_transacciones_sku ON transacciones_ventas(id_sku)",
        
        # Productos
        "CREATE INDEX IF NOT EXISTS idx_productos_categoria ON maestro_productos(categoria_nivel1)",
        "CREATE INDEX IF NOT EXISTS idx_productos_marca ON maestro_productos(marca)",
        
        # Precios
        "CREATE INDEX IF NOT EXISTS idx_precios_vigencia ON historico_precios(fecha_inicio, fecha_fin)",
        "CREATE INDEX IF NOT EXISTS idx_precios_sku_fecha ON historico_precios(id_sku, fecha_inicio)",
        
        # Inventarios
        "CREATE INDEX IF NOT EXISTS idx_inventario_fecha_sku ON niveles_inventario(fecha_corte, id_sku)",
        
        # Competencia
        "CREATE INDEX IF NOT EXISTS idx_competencia_fecha ON inteligencia_competitiva(fecha_captura)",
        "CREATE INDEX IF NOT EXISTS idx_competencia_sku ON inteligencia_competitiva(sku_propio)",
    ]
    
    with engine.connect() as conn:
        for index in indexes:
            try:
                conn.execute(text(index))
                logger.info(f"Created index: {index.split('idx_')[1].split(' ')[0]}")
            except Exception as e:
                logger.warning(f"Could not create index: {e}")
        
        conn.commit()


def main():
    """Main setup function"""
    logger.info("Starting database setup...")
    
    try:
        # 1. Create database
        create_database()
        
        # 2. Create tables
        engine = create_tables()
        
        # 3. Create extensions
        create_extensions(engine)
        
        # 4. Create indexes
        create_indexes(engine)
        
        logger.info("✅ Database setup completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()