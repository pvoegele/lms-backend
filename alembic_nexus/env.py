"""
Alembic Environment - Custom migration orchestrator
"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool as sql_pool
from alembic import context
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from warehouse_nexus.cerebrum.configuration_nucleus import extract_runtime_config
from warehouse_nexus.cerebrum.psql_conductor import EntityFoundation

# Import models
from warehouse_nexus.schema_registry import (
    core_entities, partner_entities, pricing_entities, facility_entities,
    inventory_entities, order_entities, stock_entities, audit_entities, customer_entities
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = EntityFoundation.metadata
runtime_cfg = extract_runtime_config()


def run_migrations_offline():
    context.configure(
        url=runtime_cfg.synthesize_psql_uri(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    cfg = config.get_section(config.config_ini_section)
    cfg["sqlalchemy.url"] = runtime_cfg.synthesize_psql_uri()
    
    connectable = engine_from_config(
        cfg, prefix="sqlalchemy.", poolclass=sql_pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
