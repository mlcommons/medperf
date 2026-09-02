import os
from pathlib import Path

import django
from django.conf import settings
from django.core.management import execute_from_command_line

from medperf_server import cli_postgres


def reset_database(container_name: str) -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "medperf.settings")
    django.setup()

    if settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
        db_file = Path(settings.DATABASES["default"]["NAME"])
        if db_file.exists():
            db_file.unlink()
        else:
            print(f"warning: {db_file} does not exist, nothing to delete")
    else:
        cli_postgres.recreate_container(container_name)
        cli_postgres.wait_for_postgres(container_name)

    execute_from_command_line(["medperf_server", "migrate"])
