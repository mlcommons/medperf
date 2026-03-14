from importlib import resources
import yaml
from pathlib import Path
import logging
from medperf.logging.utils import log_machine_details

import typer
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from medperf import config
from medperf.decorators import clean_except
from medperf.web_ui.common import custom_exception_handler
from medperf.utils import print_webui_props
from medperf.web_ui.datasets import router as datasets_router
from medperf.web_ui.benchmarks.routes import router as benchmarks_router
from medperf.web_ui.containers.routes import router as containers_router
from medperf.web_ui.models.routes import router as models_router
from medperf.web_ui.assets.routes import router as assets_router
from medperf.web_ui.training.routes import router as training_router
from medperf.web_ui.aggregators.routes import router as aggregators_router
from medperf.web_ui.yaml_fetch.routes import router as yaml_fetch_router
from medperf.web_ui.api.routes import router as api_router
from medperf.web_ui.security_check import router as login_router
from medperf.web_ui.events import router as events_router
from medperf.web_ui.medperf_login import router as medperf_login
from medperf.web_ui.settings import router as settings_router
from medperf.web_ui.auth import wrap_openapi, NotAuthenticatedException, security_token

UI_MODE_COOKIE = "medperf-mode"
UI_MODE_TRAINING = "training"
UI_MODE_EVALUATION = "evaluation"


class NavModeMiddleware(BaseHTTPMiddleware):
    """Set request.app.state.ui_mode from cookie so templates and routes can use it."""

    async def dispatch(self, request, call_next):
        request.app.state.ui_mode = request.cookies.get(
            UI_MODE_COOKIE, UI_MODE_EVALUATION
        )
        if request.app.state.ui_mode not in (UI_MODE_EVALUATION, UI_MODE_TRAINING):
            request.app.state.ui_mode = UI_MODE_EVALUATION
        return await call_next(request)


web_app = FastAPI()

web_app.add_middleware(NavModeMiddleware)

web_app.include_router(datasets_router, prefix="/datasets")
web_app.include_router(benchmarks_router, prefix="/benchmarks")
web_app.include_router(containers_router, prefix="/containers")
web_app.include_router(models_router, prefix="/models")
web_app.include_router(assets_router, prefix="/assets")
web_app.include_router(training_router, prefix="/training")
web_app.include_router(aggregators_router, prefix="/aggregators")
web_app.include_router(yaml_fetch_router)
web_app.include_router(api_router, prefix="/api")
web_app.include_router(login_router)
web_app.include_router(events_router)
web_app.include_router(medperf_login)
web_app.include_router(settings_router, prefix="/settings")

static_folder_path = Path(resources.files("medperf.web_ui")) / "static"

web_app.mount("/static", StaticFiles(directory=static_folder_path), name="static")

web_app.add_exception_handler(Exception, custom_exception_handler)

web_app.openapi = wrap_openapi(web_app)


@web_app.on_event("startup")
def startup_event():
    web_app.state.active_tasks = {}  # task_id -> WebUITask (multiple tasks can run)
    web_app.state.old_tasks = []  # List of [schemas.WebUITask]
    web_app.state.task_running = False
    web_app.state.MAXLOGMESSAGES = config.webui_max_log_messages

    # List of [schemas.Notification] will appear in the notifications tab
    web_app.state.notifications = []

    # Container auto grant access initial values
    web_app.state.model_auto_give_access = {
        "running": False,
        "worker": None,
        "benchmark": 0,
        "model": 0,
        "emails": "",
        "interval": 0,
    }

    # Set default UI mode to evaluation on startup, will be updated by NavModeMiddleware on each request based on cookie
    web_app.state.ui_mode = UI_MODE_EVALUATION
    web_app.state.TRAINING_MODE = UI_MODE_TRAINING
    web_app.state.EVALUATION_MODE = UI_MODE_EVALUATION

    # continue setup logging
    host_props = {**web_app.state.host_props, "security_token": security_token}
    with open(config.webui_host_props, "w") as f:
        yaml.safe_dump(host_props, f)

    # print security token to CLI (avoid logging to file)
    host = host_props["host"]
    port = host_props["port"]
    print_webui_props(host, port, security_token)

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
def read_root(request: Request):
    if request.app.state.ui_mode == UI_MODE_TRAINING:
        return RedirectResponse(url="/training/ui")
    return RedirectResponse(url="/benchmarks/ui")


@web_app.get("/set_mode", include_in_schema=False)
def set_mode(request: Request, mode: str = "evaluation"):
    """Set nav mode (evaluation | training) via cookie and redirect to the default page for that mode."""
    if mode == UI_MODE_TRAINING:
        response = RedirectResponse(url="/training/ui")
        response.set_cookie(key=UI_MODE_COOKIE, value=UI_MODE_TRAINING, path="/")
    else:
        response = RedirectResponse(url="/benchmarks/ui")
        response.set_cookie(key=UI_MODE_COOKIE, value=UI_MODE_EVALUATION, path="/")
    return response


app = typer.Typer()


@app.command("run")
@clean_except
def run(
    port: int = typer.Option(8100, "--port", help="port to use"),
):
    """Runs a local web UI"""
    import uvicorn

    host = "127.0.0.1"
    web_app.state.host_props = {"host": host, "port": port}

    uvicorn.run(
        web_app,
        host=host,
        port=port,
        log_level=config.loglevel,
    )
