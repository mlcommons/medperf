import concurrent
import dataclasses
import datetime
import hashlib
import logging
import re
import time
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from functools import cached_property
from typing import Any, Callable, Optional, Sequence

import dacite
import httpx
import tenacity
from httpx import Response
from tenacity import retry, stop_after_attempt

from baas.error_handling import (
    AuthException,
    BadRequestException,
    standard_retry,
)
from baas.universal_client import ModelClient, SinglePrompt, UniversalClient

logger = logging.getLogger(__name__)

DEFAULT_BAAS_URL = "https://baas.mlcommons.org/0.1/"

DEFAULT_LOCALE = "en_us"
SUPPORTED_LOCALES = ("en_us", "fr_fr")


def normalize_locale(locale: str | None) -> str:
    if not locale or locale.strip() == "":
        return DEFAULT_LOCALE
    normalized = locale.lower()
    if normalized not in SUPPORTED_LOCALES:
        raise ValueError(f"Unsupported locale {locale}; supported locales are: {', '.join(SUPPORTED_LOCALES)}")
    return normalized


@dataclass
class BenchmarkRunListing:
    uid: str
    status: str
    username: str
    user_email: str
    benchmark_type: str
    version: str
    sut_uid: str
    locale: str
    created: Optional[datetime.datetime]
    started: Optional[datetime.datetime]
    completed: Optional[datetime.datetime]

    @cached_property
    def display_uid(self) -> str:
        match = re.search(r"\d{8}-\d{6}", self.uid)
        if match:
            dt_part = match[0]
        else:
            dt_part = self.created.strftime("%Y%m%d-%H%M%S")

        m = hashlib.md5()
        m.update(self.uid.encode("utf-8"))
        hash_part = m.hexdigest()[-6:]
        return dt_part + "-" + hash_part

    @cached_property
    def display_sut(self) -> str:
        if self.sut_uid.endswith(":indirect"):
            return self.sut_uid[:-9]
        return self.sut_uid

    @classmethod
    def from_json(cls, parsed_json) -> "BenchmarkRunListing":
        return dacite.from_dict(
            cls,
            parsed_json,
            dacite.Config(type_hooks={datetime.datetime: lambda s: datetime.datetime.fromisoformat(s + "Z")}),
        )


class BenchmarkRun:

    def __init__(self, baas_client: "BaasClient", run_id: str) -> None:
        self._baas_client = baas_client
        self.run_id = run_id

    def get_prompts(self) -> Sequence[dict]:
        response = self._baas_client._get(f"/run/{self.run_id}/prompts")
        if response.status_code == httpx.codes.OK:
            prompts = response.json()["prompts"]
            logger.debug(f"Got prompts: {prompts}")
            return prompts
        else:
            logger.debug(f"getting prompts failed: {response}")
            return []

    def submit_responses(self, responses: list[dict]) -> None:
        logger.debug(f"Submitting responses: {responses}")
        self._baas_client._put(f"/run/{self.run_id}/responses", json=responses)

    def is_done(self) -> bool:
        return self.status() in ["success", "cancelled", "failed", "invalid image"]

    def is_success(self) -> bool:
        return self.status() == "success"

    def status(self):
        result = self._baas_client._get(f"/run/{self.run_id}/status")
        j = result.json()
        if not j:
            return None
        return j["status"]

    def get_results(self) -> Optional[dict]:
        result = self._baas_client._get(f"/run/{self.run_id}/results")
        j = result.json()
        logger.debug(f"Got results: {j}")
        if j:
            if "results" not in j:  # todo replace with something saner
                return j
        return None

    def get_annotations(self) -> Optional[dict]:
        result = self._baas_client._get(f"/run/{self.run_id}/annotations")
        if result.status_code == httpx.codes.NO_CONTENT:
            return None
        if result.status_code == httpx.codes.CONFLICT:
            return None
        j = result.json()
        logger.debug(f"Got annotations: {j}")
        return j

    def cancel(self):
        self._baas_client.cancel(self.run_id)


class BaasClient:
    def __init__(self, baas_key: str, baas_url):
        self.baas_key = baas_key
        self.baas_url = baas_url
        self._http_client = httpx.Client(
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + baas_key,
            },
            base_url=baas_url,
            timeout=httpx.Timeout(120),
        )

    def up_and_healthy(self) -> tuple[bool, str]:
        expected_errors = (httpx.HTTPError, KeyError, tenacity.RetryError)
        try:
            up = self._get("/up")
            if not (up.json() and up.json()["status"] == "up"):
                return False, "not up"
        except expected_errors as e:
            logger.debug("failed connecting to BaaS server", exc_info=True)
            return False, f"Can't reach BaaS server: {e}"

        try:
            up = self._get("/health")
            if not (up.json() and up.json()["status"] == "OK"):
                return False, "not healthy"
        except AuthException:
            return False, f"Authentication failed"
        except expected_errors:
            logger.debug("failed checking health", exc_info=True)
            return False, "not healthy"

        return True, "up"

    def start_run(self, model_id: str, mode=None, locale: str | None = None, benchmark_type: str = "general") -> BenchmarkRun:
        url = f"/run/benchmark/{benchmark_type}"
        if mode:
            url += f"/{mode}"
        resp: Response = self._post(url, {"model_id": model_id, "locale": normalize_locale(locale)})
        j = resp.json()
        run_id = j["run_id"]
        return BenchmarkRun(self, run_id)

    def resume_run(self, run_id):
        return BenchmarkRun(self, run_id)

    def get_run_listings(self) -> Sequence[BenchmarkRunListing]:
        resp: Response = self._get("/run")
        j = resp.json()
        if not j:
            return []
        return [BenchmarkRunListing.from_json(i) for i in j]

    def get_run(self, run_id: str) -> BenchmarkRun:
        run_listings = self.get_run_listings()
        matching = [l for l in run_listings if run_id in l.display_uid or run_id in l.uid]

        if not matching:
            raise ValueError(f"No run with id {run_id}")
        if len(matching) > 1:
            raise ValueError(f"Multiple matches for {run_id}: {[l.display_uid for l in matching]}")
        return BenchmarkRun(self, matching[0].uid)

    def cancel(self, run_id: str) -> None:
        try:
            _ = self._delete(f"/run/{run_id}")
        except Exception as e:
            print(e)

    def _raise_for_status(self, resp: httpx.Response):
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthException(f"Problem with BaaS auth {self.baas_key}") from e
            else:
                if e.response.content:
                    raise BadRequestException(e.response.content.decode())
                else:
                    raise
        except:
            raise

    @standard_retry
    def _get(self, path) -> httpx.Response:
        resp = self._http_client.get(path)
        self._raise_for_status(resp)
        return resp

    @standard_retry
    def _post(self, path, json) -> httpx.Response:
        resp: Response = self._http_client.post(path, json=json)
        self._raise_for_status(resp)
        return resp

    @standard_retry
    def _put(self, path, json) -> httpx.Response:
        resp: Response = self._http_client.put(path, json=json)
        self._raise_for_status(resp)
        return resp

    @standard_retry
    def _delete(self, path) -> httpx.Response:
        resp: Response = self._http_client.delete(path)
        self._raise_for_status(resp)
        return resp


class PromptRunner:
    def __init__(
        self,
        run: BenchmarkRun,
        model_client: ModelClient,
        progress_function: Callable[[int], None] = lambda x: None,
        no_faster_than: float = 1,
    ):
        self.no_faster_than = no_faster_than
        self.benchmark_run = run
        self.model_client = model_client
        self.progress_function = progress_function
        self.total_prompts_processed = 0

    def run(self):
        while not (max_workers := len(self.benchmark_run.get_prompts())):
            logger.debug("Waiting for prompts")
            time.sleep(1)
        pool = ThreadPoolExecutor(max_workers=max_workers)
        prompts_to_futures: dict[SinglePrompt, Future] = {}

        def run_one(prompt: SinglePrompt):
            return prompt, self.model_client.request(prompt)

        while not self.benchmark_run.is_done():
            loop_start = time.time()
            new_prompts = self._get_new_prompts(prompts_to_futures)
            logger.debug(
                f"starting loop with {self.total_prompts_processed} finished, {len(prompts_to_futures)} in flight, and {len(new_prompts)} new"
            )

            for prompt in new_prompts:
                prompts_to_futures[prompt] = pool.submit(run_one, prompt)

            responses = self._process_responses(prompts_to_futures)
            if responses:
                self._submit_responses(responses)

            loop_duration = time.time() - loop_start
            logger.debug(f"loop took {loop_duration:.2f} seconds")
            if loop_duration < self.no_faster_than:
                time.sleep(self.no_faster_than - loop_duration)

    @retry(stop=stop_after_attempt(5))
    def _get_new_prompts(self, prompts_to_futures: dict[SinglePrompt, Future]) -> list[SinglePrompt]:
        prompts = [SinglePrompt.from_baas_request(p) for p in self.benchmark_run.get_prompts()]
        new_prompts = [p for p in prompts if p not in prompts_to_futures]
        return new_prompts

    def _process_responses(self, prompts_to_futures: dict[SinglePrompt, Future]) -> list[Any]:
        futures = concurrent.futures.wait(prompts_to_futures.values(), timeout=1)
        responses = []
        for result in futures.done:
            if result.done():
                prompt, response = result.result()
                responses.append(response)
                del prompts_to_futures[prompt]
        return responses

    @retry(stop=stop_after_attempt(5))
    def _submit_responses(self, responses: list[Any]):
        self.benchmark_run.submit_responses([dataclasses.asdict(r) for r in responses])
        self.total_prompts_processed += len(responses)
        self.progress_function(self.total_prompts_processed)


def run_a_benchmark(
    model_key: str,
    model_url: str,
    model_id: str,
    baas_key: str,
    baas_url: str = DEFAULT_BAAS_URL,
    mode: str | None = None,
    locale: str | None = None,
    benchmark_type: str = "general",
) -> dict | None:
    """
    Runs a full benchmark, as the CLI does, but with no console output or progress
    updates. See the cli for explanation of the input parameters. If the job is successful,
    returns the parsed results JSON; otherwise, returns None.
    """

    model_client = UniversalClient(model_url, model_key, model_id)
    baas_client = BaasClient(baas_key, baas_url)
    run = baas_client.start_run(model_id, mode, locale, benchmark_type)
    PromptRunner(run, model_client).run()
    return {"results": run.get_results(), "annotations": run.get_annotations()}
