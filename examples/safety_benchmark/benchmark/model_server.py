"""Runs a model folder's `run.sh`, and stops it again.

A model folder is swappable. What it owes the benchmark is an executable
`run.sh` that accepts `--port`, answers `GET /health` once it is ready to
work, and exits on SIGTERM. Everything else about it is its own business.

One model folder is up at a time, and only for as long as it is being asked
questions -- the benchmark starts it, relays a run through it, and stops it.
"""

import contextlib
import os
import signal
import subprocess
import time

import requests

STARTUP_TIMEOUT_SECONDS = 1800
SHUTDOWN_TIMEOUT_SECONDS = 60
POLL_SECONDS = 2


@contextlib.contextmanager
def serve(folder: str, port: int, *extra_args: str):
    command = [os.path.join(folder, "run.sh"), "--port", str(port), *extra_args]
    process = subprocess.Popen(command, start_new_session=True)
    base_url = f"http://127.0.0.1:{port}"
    try:
        _wait_until_healthy(process, base_url)
        yield base_url
    finally:
        _stop(process)


def _wait_until_healthy(process: subprocess.Popen, base_url: str) -> None:
    deadline = time.time() + STARTUP_TIMEOUT_SECONDS
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                f"{base_url} exited with code {process.returncode} before serving"
            )
        try:
            if requests.get(f"{base_url}/health", timeout=5).ok:
                return
        except requests.RequestException:
            pass
        time.sleep(POLL_SECONDS)
    raise TimeoutError(f"{base_url} was not ready within {STARTUP_TIMEOUT_SECONDS}s")


def _stop(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    # The whole group: a server may have forked workers of its own.
    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    try:
        process.wait(timeout=SHUTDOWN_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        process.wait()
