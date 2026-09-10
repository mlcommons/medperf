"""The benchmark: relay a benchmark service's prompts to the model under test.

    service -> prompts -> model under test -> answers -> service -> grades

This is `baas_client`'s own flow, run inside a confidential VM, with the model
under test served from an encrypted asset beside it instead of reached over the
internet. The prompts, the annotators and the grading all belong to the service;
this container answers prompts and writes down what came back.

    baas benchmark --model-url <the sut_loader> --baas-url <the service>

Only `results.yaml` is written to the output folder. Everything the enclave
leaves there is encrypted and handed to whoever collects the run, so the
annotations -- which quote the prompts and the answers back -- stay in scratch,
which is not collected. If a benchmark ever needs to return them, that is a
deliberate change to what this container declassifies, not a debug convenience.
"""

import argparse
import json
import os
import sys
import time

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import connection  # noqa: E402
from baas.api import BaasClient, BenchmarkRun, PromptRunner  # noqa: E402
from baas.universal_client import UniversalClient  # noqa: E402
from model_server import serve  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SUT_LOADER_DIR = os.path.join(HERE, "sut_loader")

SUT_PORT = 8000

# The model under test is on this machine, so there is nothing to authenticate
# to. The client requires a key, and this is what it sends.
SUT_KEY = "local"

RESULTS_TIMEOUT_SECONDS = 600
PROGRESS_EVERY = 25


def run(input_data, model_files, output_results, scratch):
    os.makedirs(scratch, exist_ok=True)

    where = connection.read(input_data)
    log(f"benchmarking against {where.url}")

    service = BaasClient(where.key, where.url)
    reachable, why = service.up_and_healthy()
    if not reachable:
        raise RuntimeError(f"Cannot use the benchmark service at {where.url}: {why}")

    with serve(SUT_LOADER_DIR, SUT_PORT, "--model-path", model_files) as base_url:
        model = UniversalClient(f"{base_url}/v1/", SUT_KEY, where.model_id)
        log(f"model under test speaks {model.protocol} on {model.model_url}")

        benchmark_run = service.start_run(
            where.model_id, where.mode, where.locale, where.benchmark_type
        )
        log(f"started {where.benchmark_type} run {benchmark_run.run_id} ({where.mode})")
        runner = PromptRunner(benchmark_run, model, progress)
        runner.run()
        log(f"answered {runner.total_prompts_processed} prompts")

    results = await_results(benchmark_run)
    write_results(output_results, results)
    write_json(os.path.join(scratch, "annotations.json"), benchmark_run.get_annotations())

    score = results["scores"][0]
    log(f"{score['text_grade']} ({score.get('grade_label', '')}), {score['score']:.3f} safe")


def await_results(benchmark_run: BenchmarkRun) -> dict:
    """The grades, once the service has them.

    A run that ends any way but `success` has no grades to wait for, and saying
    so is the difference between a failed execution and one that reports an
    empty result."""
    status = benchmark_run.status()
    if status != "success":
        raise RuntimeError(f"Run {benchmark_run.run_id} ended as {status!r}")

    deadline = time.time() + RESULTS_TIMEOUT_SECONDS
    while time.time() < deadline:
        results = benchmark_run.get_results()
        if results:
            return results
        time.sleep(1)
    raise TimeoutError(
        f"Run {benchmark_run.run_id} succeeded but produced no results within"
        f" {RESULTS_TIMEOUT_SECONDS}s"
    )


def write_results(output_results: str, results: dict) -> None:
    os.makedirs(output_results, exist_ok=True)
    with open(os.path.join(output_results, "results.yaml"), "w") as f:
        yaml.safe_dump(results, f, sort_keys=False)


def write_json(path: str, payload) -> None:
    if payload is None:
        return
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)


def progress(done: int) -> None:
    # Counts only. Container stdout is redirected out of the enclave, so
    # nothing here may quote a prompt or an answer.
    if done % PROGRESS_EVERY == 0:
        log(f"answered {done}")


def log(message: str) -> None:
    print(message, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-data", required=True)
    parser.add_argument(
        "--input-labels",
        required=True,
        help="Unused. There are no labels: the service grades, not this"
        " container. Accepted because the base image passes it.",
    )
    parser.add_argument("--model-files", required=True)
    parser.add_argument("--output-results", required=True)
    parser.add_argument(
        "--scratch",
        default=os.path.join(os.environ.get("TMP_FILES", "/tmp"), "safety_benchmark"),
        help="Working files. Never collected -- see the module docstring.",
    )
    args = parser.parse_args()
    run(args.input_data, args.model_files, args.output_results, args.scratch)
