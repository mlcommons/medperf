from importlib import resources
from pathlib import Path

import typer
from fastapi import FastAPI, APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from medperf import settings
from medperf.decorators import clean_except
from medperf.web_ui.common import custom_exception_handler
from medperf.web_ui.datasets.routes import router as datasets_router
from medperf.web_ui.benchmarks.routes import router as benchmarks_router
from medperf.web_ui.mlcubes.routes import router as mlcubes_router
from medperf.web_ui.yaml_fetch.routes import router as yaml_fetch_router
from medperf.web_ui.profile.routes import router as profile_router

web_app = FastAPI()

web_app.include_router(datasets_router, prefix="/datasets")
web_app.include_router(benchmarks_router, prefix="/benchmarks")
web_app.include_router(mlcubes_router, prefix="/mlcubes")
web_app.include_router(yaml_fetch_router)
web_app.include_router(profile_router)

static_folder_path = Path(resources.files("medperf.web_ui")) / "static"  # noqa
web_app.mount(
    "/static",
    StaticFiles(
        directory=static_folder_path,
    )
)

web_app.add_exception_handler(Exception, custom_exception_handler)


@web_app.get("/", include_in_schema=False)
def read_root():
    return RedirectResponse(url="/benchmarks/ui")


app = typer.Typer()


@app.command("run")
@clean_except
def run(
        port: int = typer.Option(8100, "--port", help="port to use"),
):
    """Runs a local web UI"""
    import uvicorn
    uvicorn.run(web_app, host="127.0.0.1", port=port, log_level=settings.loglevel)
