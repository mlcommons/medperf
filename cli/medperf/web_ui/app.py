from importlib import resources
from pathlib import Path
import logging
from medperf.logging.utils import log_machine_details

import typer
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from medperf import config

from medperf.decorators import clean_except
from medperf.web_ui.common import custom_exception_handler
from medperf.web_ui.datasets import router as datasets_router
from medperf.web_ui.benchmarks.routes import router as benchmarks_router
from medperf.web_ui.containers.routes import router as containers_router
from medperf.web_ui.yaml_fetch.routes import router as yaml_fetch_router
from medperf.web_ui.api.routes import router as api_router
from medperf.web_ui.security_check import router as login_router
from medperf.web_ui.events import router as events_router
from medperf.web_ui.medperf_login import router as medperf_login
from medperf.web_ui.profiles import router as profiles_router
from medperf.web_ui.auth import wrap_openapi, NotAuthenticatedException

web_app = FastAPI()

web_app.include_router(datasets_router, prefix="/datasets")
web_app.include_router(benchmarks_router, prefix="/benchmarks")
web_app.include_router(containers_router, prefix="/containers")
web_app.include_router(yaml_fetch_router)
web_app.include_router(api_router, prefix="/api")
web_app.include_router(login_router)
web_app.include_router(events_router)
web_app.include_router(medperf_login)
web_app.include_router(profiles_router, prefix="/profiles")

static_folder_path = Path(resources.files("medperf.web_ui")) / "static"

web_app.mount("/static", StaticFiles(directory=static_folder_path), name="static")

web_app.add_exception_handler(Exception, custom_exception_handler)

web_app.openapi = wrap_openapi(web_app)


@web_app.on_event("startup")
def startup_event():
    # Initialize state variales for:
    # Showing logs/prompts
    # Checking if a CLI function is running
    # Notify user about a finished or a running task / pending prompt-confirmation
    web_app.state.task = {
        "id": "",
        "name": "",
        "running": False,
        "logs": [],
        "formData": {},
    }
    web_app.state.old_tasks = []
    web_app.state.task_running = False
    # Will be shown in the notifications tab in the navbar
    web_app.state.notifications = []
    # notifications to be sent will be in state.new_notifications. unpon sending, they'll be moved to state.notifications
    web_app.state.new_notifications = []
    # A notifications will be a list of dictionaries as follows:
    # {
    # "id": "Unique id for each notification",
    # "message": "Task X is finished / Failed to do task X",
    # "type": "success/error/info(for prompt)".
    # "url": "to navigate to the finished task page",
    # "read": bool,
    # "time": "timestamp"
    # }

    # continue setup logging
    loglevel = config.loglevel.upper()
    logging.getLogger().setLevel(loglevel)
    logging.getLogger("requests").setLevel(loglevel)
    log_machine_details()


@web_app.exception_handler(NotAuthenticatedException)
def not_authenticated_exception_handler(
    request: Request, exc: NotAuthenticatedException
):
    return RedirectResponse(url=exc.redirect_url)


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

    uvicorn.run(
        web_app,
        host="127.0.0.1",
        port=port,
        log_level=config.loglevel,
    )
