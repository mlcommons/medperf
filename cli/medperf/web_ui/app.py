from importlib import resources
from pathlib import Path

from medperf.account_management.account_management import read_user_account
import typer
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from medperf import config
from medperf.ui.factory import UIFactory

from medperf.decorators import clean_except
from medperf.web_ui.common import custom_exception_handler, templates
from medperf.web_ui.datasets import router as datasets_router
from medperf.web_ui.benchmarks.routes import router as benchmarks_router
from medperf.web_ui.mlcubes.routes import router as mlcubes_router
from medperf.web_ui.yaml_fetch.routes import router as yaml_fetch_router
from medperf.web_ui.api.routes import router as api_router
from medperf.web_ui.login import router as login_router
from medperf.web_ui.events import router as events_router
from medperf.web_ui.medperf_login import router as medperf_login
from medperf.web_ui.profiles import router as profiles_router
from medperf.web_ui.auth import security_token, wrap_openapi, NotAuthenticatedException

web_app = FastAPI()

web_app.include_router(datasets_router, prefix="/datasets")
web_app.include_router(benchmarks_router, prefix="/benchmarks")
web_app.include_router(mlcubes_router, prefix="/mlcubes")
web_app.include_router(yaml_fetch_router)
web_app.include_router(api_router, prefix="/api")
web_app.include_router(login_router)
web_app.include_router(events_router)
web_app.include_router(medperf_login)
web_app.include_router(profiles_router)

static_folder_path = Path(resources.files("medperf.web_ui")) / "static"
web_app.mount(
    "/static",
    StaticFiles(
        directory=static_folder_path,
    ),
)

web_app.add_exception_handler(Exception, custom_exception_handler)

web_app.openapi = wrap_openapi(web_app)


@web_app.on_event("startup")
def startup_event():

    # print security token to CLI (avoid logging to file)
    print("=" * 40)
    print()
    print("Use security token to view the web-UI:")
    print(security_token)
    print()
    print("=" * 40)


@web_app.exception_handler(NotAuthenticatedException)
def not_authenticated_exception_handler(
    request: Request, exc: NotAuthenticatedException
):
    return RedirectResponse(url=exc.redirect_url)


@web_app.get("/", include_in_schema=False)
def read_root():
    return RedirectResponse(url="/benchmarks/ui")


def is_logged_in():
    return read_user_account() is not None


templates.env.globals["logged_in"] = (
    is_logged_in()
)  # check for cleaner solution like middlewares

app = typer.Typer()


@app.command("run")
@clean_except
def run(
    port: int = typer.Option(8100, "--port", help="port to use"),
):
    """Runs a local web UI"""
    import uvicorn

    config.ui = UIFactory.create_ui(config.webui)

    uvicorn.run(
        web_app,
        host="127.0.0.1",
        port=port,
        log_level=config.loglevel,
    )
