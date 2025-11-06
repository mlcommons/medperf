from __future__ import annotations
import os
from airflow.sdk.api.client import BearerAuth as AirflowBearerAuth
from typing import Optional
from methodtools import lru_cache
import time
import httpx
from pydantic import SecretStr

"""
The AirflowAPIClient defined in this Module if structured similarly to the internal
Client class used by Airflow (i.e airflow.sdk.api.client.Client), but simplified
so that only methods necessary for the Airflow <> MedPerf integration are 
implemented.
"""


class BearerAuth(AirflowBearerAuth):
    def __init__(
        self,
        token: str,
        expires_at: Optional[float] = None,
        leeway_seconds: float = None,
    ):
        if expires_at is None:
            twenty_four_hours = 60 * 60 * 24  # Default duration from airflow
            token_duration = os.getenv(
                "AIRFLOW__API_AUTH__JWT_EXPIRATION_TIME", twenty_four_hours
            )

            leeway_seconds = leeway_seconds or 30
            now = time.time()
            expires_at = now + token_duration + leeway_seconds

        self.expires_at = expires_at
        super().__init__(token=token)

    def is_valid(self):
        now = time.time()
        return now < self.expires_at


class AirflowAPIClient(httpx.Client):

    def __init__(
        self,
        username: str,
        password: SecretStr,
        api_url: str,
        **kwargs,
    ):
        self.username = username
        self.password = password
        token = self._get_token(api_url)
        auth = BearerAuth(token)
        event_hooks = {"request": [self.renew_token]}
        super().__init__(base_url=api_url, auth=auth, event_hooks=event_hooks, **kwargs)

    def _get_token(self, base_url):
        if base_url is None:
            return ""

        base_for_auth = base_url.split("/api")[0]
        headers = {"Content-Type": "application/json"}
        data = {"username": self.username, "password": self.password.get_secret_value()}

        auth_url = f"{base_for_auth}/auth/token"
        response = httpx.post(auth_url, headers=headers, json=data)

        if response.status_code != 201:
            print("Failed to get token:", response.status_code, response.text)
        jwt_token = response.json().get("access_token")
        return jwt_token

    def renew_token(self, request: httpx.Request):
        if not self.auth.is_valid():
            new_token = self._get_token(str(self.base_url))
            self.auth.token = new_token
            request.headers["Authorization"] = "Bearer " + self.auth.token

    @lru_cache()
    @property
    def dags(self) -> DagOperations:
        return DagOperations(self)

    @lru_cache()
    @property
    def dag_runs(self) -> DagRunOperations:
        return DagRunOperations(self)

    @lru_cache()
    @property
    def task_instances(self) -> TaskInstanceOperations:
        return TaskInstanceOperations(self)

    @lru_cache()
    @property
    def tasks(self) -> TaskOperations:
        return TaskOperations(self)

    @lru_cache()
    @property
    def assets(self) -> AssetOperations:
        return AssetOperations(self)


class BaseOperations:
    __slots__ = ("client",)

    def __init__(self, client: AirflowAPIClient):
        self.client = client


class DagOperations(BaseOperations):

    def get_all_dags(self):
        return self.client.get("dags").json()


class DagRunOperations(BaseOperations):

    def get_most_recent_dag_run(self, dag_id: str):
        params = {"dag_id": dag_id, "limit": 1, "order_by": "logical_date"}
        return self.client.get(f"dags/{dag_id}/dagRuns", params=params).json()

    def get_dag_run_by_run_id(self, dag_id: str, dag_run_id: str):
        return self.client.get(f"dags/{dag_id}/dagRuns/{dag_run_id}").json()

    def trigger_dag_run(self, dag_id: str):
        json_data = {"logical_date": None}
        response = self.client.post(f"dags/{dag_id}/dagRuns", json=json_data)
        return response.json()


class TaskInstanceOperations(BaseOperations):
    def get_task_instances_in_dag_run(self, dag_id: str, dag_run_id: str):
        return self.client.get(
            f"dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances"
        ).json()


class TaskOperations(BaseOperations):
    def get_tasks(self, dag_id: str):
        return self.client.get(f"dags/{dag_id}/tasks").json()


class AssetOperations(BaseOperations):

    def get_asset_events(self):
        return self.client.get("assets/events").json()
