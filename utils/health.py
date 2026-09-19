from pathlib import Path

from config.settings import DATABASE_PATH


def check_project_health() -> dict:
    checks = {}

    checks["database_directory"] = DATABASE_PATH.parent.exists()
    checks["database_file"] = DATABASE_PATH.exists()

    return checks


def project_is_healthy() -> bool:
    checks = check_project_health()

    return all(checks.values())