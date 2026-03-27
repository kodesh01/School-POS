from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings

logger = logging.getLogger(__name__)


async def ensure_database_exists() -> None:
    """
    Create the database if it doesn't exist.

    Connects to master and runs CREATE DATABASE. Safe to run on startup.
    """
    engine = create_async_engine(
        settings.sqlalchemy_master_uri,
        pool_pre_ping=True,
        pool_size=2,
        max_overflow=5,
        pool_recycle=1800,
        echo=False,
        future=True,
    )

    db_name_escaped = settings.sqlserver_db_name.replace("]", "]]")
    check_sql = text("SELECT 1 FROM sys.databases WHERE name = :name")
    create_sql = text(f"CREATE DATABASE [{db_name_escaped}]")

    async with engine.connect() as conn:
        res = await conn.execute(check_sql, {"name": settings.sqlserver_db_name})
        exists = res.scalar() is not None
        if not exists:
            logger.info("Database %s not found; creating...", settings.sqlserver_db_name)
            # SQL Server doesn't allow CREATE DATABASE inside a transaction
            await conn.rollback()
            await conn.execution_options(isolation_level="AUTOCOMMIT")
            await conn.execute(create_sql)
            logger.info("Database created.")
        else:
            logger.info("Database %s exists.", settings.sqlserver_db_name)

    await engine.dispose()

