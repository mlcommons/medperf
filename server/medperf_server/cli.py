from pathlib import Path
from typing import Optional

import typer

from medperf_server.cli_certs import ensure_cert
from medperf_server.cli_credentials import ensure_mock_credentials
from medperf_server.cli_config import set_config
from medperf_server.cli_db import reset_database
from medperf_server.cli_dev_server import start_server
from seed import seed as run_seed

app = typer.Typer()


@app.command("start")
def start(
    cert_file: str = typer.Option(
        "cert.crt", help="Path to write/read the SSL certificate"
    ),
    key_file: str = typer.Option(
        "cert.key", help="Path to write/read the SSL private key"
    ),
    regenerate_cert: bool = typer.Option(
        False,
        help="Replace the SSL certificate even if one exists (clients must re-trust it)",
    ),
    reset_db: bool = typer.Option(False, help="Reset the database before starting"),
    container_name: str = typer.Option(
        "postgreserver",
        help="Dev postgres container name (only used if the active config is postgres-backed)",
    ),
):
    """Run migrations, collect static files, and start the local HTTPS dev server."""
    try:
        start_server(cert_file, key_file, regenerate_cert, reset_db, container_name)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command("gen_cert")
def gen_cert_command(
    cert_file: str = typer.Option(
        "cert.crt", help="Path to write/read the SSL certificate"
    ),
    key_file: str = typer.Option(
        "cert.key", help="Path to write/read the SSL private key"
    ),
    regenerate: bool = typer.Option(
        False, help="Replace the certificate even if one exists"
    ),
):
    """Generate the self-signed dev SSL certificate, if it isn't there yet."""
    try:
        ensure_cert(cert_file, key_file, regenerate)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command("gen_credentials")
def gen_credentials_command():
    """Generate the mock login keypair and tokens the local-auth configs use."""
    try:
        ensure_mock_credentials()
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command("reset_db")
def reset_db_command(
    container_name: str = typer.Option(
        "postgreserver", help="Dev postgres container name (only used if the active config is postgres-backed)"
    ),
):
    """Delete and recreate the database, then run migrations."""
    try:
        reset_database(container_name)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command("set_config")
def set_config_command(
    config: str = typer.Argument(
        ..., help="Configuration to switch to: postgresql, sqlite, or online-auth"
    ),
    container_name: str = typer.Option(
        "postgreserver", help="Dev postgres container name (only used for postgres-backed configs)"
    ),
):
    """Switch the active local configuration by copying a bundled .env template to ~/.medperf_dev/.env."""
    if config not in ("postgresql", "sqlite", "online-auth"):
        raise typer.BadParameter("config must be one of: postgresql, sqlite, online-auth")

    try:
        set_config(config, container_name)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command("seed")
def seed_command(
    server: str = typer.Option(
        "https://127.0.0.1:8000", help="Server host address to connect"
    ),
    cert: Optional[str] = typer.Option(
        None,
        help="Server certificate (defaults to ~/.medperf_dev/cert.crt if present, else unverified)",
    ),
    version: Optional[str] = typer.Option(
        None, help="Server version to validate against"
    ),
    auth: str = typer.Option("local", help="Authentication mode: local or online"),
    demo: str = typer.Option(
        "data", help="Demo scope: benchmark, model, data, or tutorial"
    ),
    tokens: str = typer.Option(
        str(Path.home() / ".medperf_dev" / "mock_tokens" / "tokens.json"),
        help="Path to local tokens file",
    ),
    containers_assets_path: Optional[str] = typer.Option(
        None,
        help="Path to folder containing container asset files (required for --demo model/data)",
    ),
):
    """Seed the database with demo entries for integration tests or tutorials."""
    if auth not in ("local", "online"):
        raise typer.BadParameter("--auth must be 'local' or 'online'")
    if demo not in ("benchmark", "model", "data", "tutorial"):
        raise typer.BadParameter(
            "--demo must be one of: benchmark, model, data, tutorial"
        )

    if cert is None:
        default_cert = Path.home() / ".medperf_dev" / "cert.crt"
        if default_cert.exists():
            cert = str(default_cert)
        else:
            typer.echo(
                "warning: no --cert given and ~/.medperf_dev/cert.crt not found; "
                "proceeding without server certificate verification"
            )

    if containers_assets_path is None and demo in ("model", "data"):
        # Check both cwd itself (e.g. run from the repo root) and one level
        # up (e.g. run from server/, where the assets live at ../examples).
        for candidate in (
            Path("examples") / "chestxray_tutorial",
            Path("..") / "examples" / "chestxray_tutorial",
        ):
            if candidate.exists():
                containers_assets_path = str(candidate)
                break
        else:
            raise typer.BadParameter(
                "--containers-assets-path is required (no examples/chestxray_tutorial "
                "found relative to the current directory or its parent)"
            )

    try:
        run_seed(
            server=server,
            cert=cert,
            version=version,
            auth=auth,
            demo=demo,
            tokens=tokens,
            containers_assets_path=containers_assets_path,
        )
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
