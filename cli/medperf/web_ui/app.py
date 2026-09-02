from importlib import resources
import asyncio
import contextlib
import os
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
from medperf.update_manager import UpdateManager
from medperf.utils import print_webui_props
from medperf.web_ui.datasets.routes import router as datasets_router
from medperf.web_ui.benchmarks.routes import router as benchmarks_router
from medperf.web_ui.containers.routes import router as containers_router
from medperf.web_ui.models.routes import router as models_router
from medperf.web_ui.assets.routes import router as assets_router
from medperf.web_ui.schemas import WebUITask
from medperf.web_ui.training.routes import router as training_router
from medperf.web_ui.aggregators.routes import router as aggregators_router
from medperf.web_ui.api.routes import router as api_router
from medperf.web_ui.security_check import router as login_router
from medperf.web_ui.events import router as events_router
from medperf.web_ui.medperf_login import router as medperf_login
from medperf.web_ui.settings import router as settings_router
from medperf.web_ui.auth import wrap_openapi, NotAuthenticatedException, security_token

JS_VERSION = "1.0.4"

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
web_app.include_router(api_router, prefix="/api")
web_app.include_router(login_router)
web_app.include_router(events_router)
web_app.include_router(medperf_login)
web_app.include_router(settings_router, prefix="/settings")

static_folder_path = Path(resources.files("medperf.web_ui")) / "static"

web_app.mount(
    f"/static/v{JS_VERSION}", StaticFiles(directory=static_folder_path), name="static"
)

web_app.add_exception_handler(Exception, custom_exception_handler)

web_app.openapi = wrap_openapi(web_app)


async def _refresh_update_check_periodically():
    """Refreshes cached PyPI update info off the request path.

    Runs on its own schedule instead of a per-request middleware, which used
    to block the ASGI event loop on every request (including every static
    asset) with a synchronous cache-file read, and roughly every 4h with a
    blocking network call to PyPI.
    """
    while True:
        await asyncio.sleep(config.webui_update_check_interval_seconds)
        try:
            web_app.state.update_check = await asyncio.to_thread(
                UpdateManager().get_update_info, force_refresh=True
            )
        except Exception:
            logging.exception("Failed to refresh update check info")


@web_app.on_event("startup")
def startup_event():
    web_app.state.task = WebUITask()
    web_app.state.old_tasks = []  # List of [schemas.WebUITask]
    web_app.state.task_running = False
    web_app.state.update_in_progress = False
    web_app.state.update_error = None
    # Set by UpdateManager.schedule_webui_update right before it sends this
    # process SIGTERM; shutdown_event() execs it once uvicorn has drained
    # in-flight requests and finished its own shutdown.
    web_app.state.pending_restart_argv = None
    web_app.state.MAXLOGMESSAGES = config.webui_max_log_messages

    # Computed once here (blocking is fine pre-startup) and kept fresh by a
    # background task
    web_app.state.update_check = UpdateManager().get_update_info()
    web_app.state.update_check_task = asyncio.create_task(
        _refresh_update_check_periodically()
    )

    # {benchmark_id: dict} (checks if mounted and files changed)
    web_app.state.dashboards = {}

    # List of [schemas.Notification] will appear in the notifications tab
    web_app.state.notifications = []

    # List of [schemas.Event]
    web_app.state.global_events = []

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


@web_app.on_event("shutdown")
async def shutdown_event():
    web_app.state.update_check_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await web_app.state.update_check_task

    restart_argv = web_app.state.pending_restart_argv
    if restart_argv:
        os.execv(restart_argv[0], restart_argv)


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
