import os

from django.core.management import execute_from_command_line

from medperf_server import cli_certs, cli_db


def start_server(
    cert_file: str,
    key_file: str,
    regenerate_cert: bool,
    reset_db: bool,
    container_name: str,
) -> None:
    is_reloaded_process = os.environ.get("WERKZEUG_RUN_MAIN") == "true"

    if not is_reloaded_process:
        if reset_db:
            cli_db.reset_database(container_name)

        cli_certs.ensure_cert(cert_file, key_file, regenerate_cert)

        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "medperf.settings")
        execute_from_command_line(["medperf_server", "migrate"])
        execute_from_command_line(["medperf_server", "collectstatic", "--noinput"])

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "medperf.settings")
    execute_from_command_line(
        [
            "medperf_server",
            "runserver_plus",
            "--cert-file",
            cert_file,
            "--key-file",
            key_file,
        ]
    )
