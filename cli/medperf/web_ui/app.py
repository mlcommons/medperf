import typer
from fastapi import FastAPI

from medperf import config
from medperf.decorators import clean_except
from medperf.web_ui.datasets.routes import router as datasets_router
from medperf.web_ui.benchmarks.routes import router as benchmarks_router
from medperf.web_ui.mlcubes.routes import router as mlcubes_router

web_app = FastAPI()

web_app.include_router(datasets_router, prefix="/datasets")
web_app.include_router(benchmarks_router, prefix="/benchmarks")
web_app.include_router(mlcubes_router, prefix="/mlcubes")

app = typer.Typer()


@app.command("run")
@clean_except
def run(
        port: int = typer.Option(8100, "--port", help="port to use"),
):
    """Runs a local web UI"""
    import uvicorn
    uvicorn.run(web_app, host="127.0.0.1", port=port, log_level=config.loglevel)
