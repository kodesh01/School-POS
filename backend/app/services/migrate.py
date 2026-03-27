from __future__ import annotations

import os

from alembic import command
from alembic.config import Config


def run_migrations() -> None:
    """
    Run Alembic migrations (upgrade head).

    Controlled via AUTO_MIGRATE env var. Default: true for local dev.
    """
    auto = os.getenv("AUTO_MIGRATE", "true").lower() in {"1", "true", "yes", "on"}
    if not auto:
        return

    cfg = Config("backend/alembic.ini")
    cfg.set_main_option("script_location", "backend/alembic")
    command.upgrade(cfg, "head")

