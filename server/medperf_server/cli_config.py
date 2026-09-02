import shutil
from importlib import resources
from pathlib import Path

from medperf_server import cli_credentials, cli_postgres

TEMPLATE_NAMES = {
    "postgresql": ".env.local.local-auth",
    "sqlite": ".env.local.local-auth.sqlite",
    "online-auth": ".env.local.online-auth",
}
# Configs whose template sets AUTH_VERIFYING_KEY_FILE
LOCAL_AUTH_CONFIGS = {"postgresql", "sqlite"}


def set_config(config: str, container_name: str) -> None:
    template = (
        resources.files("medperf_server") / "env_templates" / TEMPLATE_NAMES[config]
    )
    dest = Path.home() / ".medperf_dev" / ".env"
    dest.parent.mkdir(parents=True, exist_ok=True)
    with resources.as_file(template) as template_path:
        shutil.copy(template_path, dest)

    if config in LOCAL_AUTH_CONFIGS:
        cli_credentials.ensure_mock_credentials()

    if config != "sqlite":
        just_started = cli_postgres.ensure_running(container_name)
        if just_started:
            cli_postgres.wait_for_postgres(container_name)
