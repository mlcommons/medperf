from airflow.plugins_manager import AirflowPlugin
from fastapi import FastAPI, Query, Request, status
from fastapi.responses import RedirectResponse
from airflow.api_fastapi.auth.managers.base_auth_manager import COOKIE_NAME_JWT_TOKEN
from medperf.containers.runners.airflow_runner_utils.airflow_api_client import (
    AirflowAPIClient,
)
from airflow.configuration import conf

app = FastAPI()


@app.get("/auto_login", status_code=status.HTTP_302_FOUND)
async def root(
    request: Request, user: str = Query(...), password: str = Query(...)
) -> RedirectResponse:
    host = conf.get("api", "host")
    port = conf.get("api", "port")
    homepage_url = f"http://{host}:{port}"
    api_url = f"{homepage_url}/api/v2"
    with AirflowAPIClient(username=user, password=password, api_url=api_url) as client:
        token = client.get_token()

    response = RedirectResponse(url=homepage_url, status_code=status.HTTP_302_FOUND)

    response.set_cookie(
        key=COOKIE_NAME_JWT_TOKEN,
        value=token,
        path="/",
    )

    return response


app_with_metadata = {
    "app": app,
    "url_prefix": "/medperf",
    "name": "Auto Login for MedPerf",
}


class AutoLoginPlugin(AirflowPlugin):
    name = "auto_login"
    fastapi_apps = [app_with_metadata]
