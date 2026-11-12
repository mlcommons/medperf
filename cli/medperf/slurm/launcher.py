import json
import logging
import os
import platform
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional

from colorama import Fore, Style

from medperf import config
from medperf.exceptions import ExecutionError, InvalidArgumentError
from medperf.utils import generate_tmp_uid
from . import commands
from .commands import JobRef, JobStatus
from .job_script import (
    EXIT_ARCH_MISMATCH,
    EXIT_CODE_FILENAME,
    EXIT_PATH_NOT_VISIBLE,
    EXIT_RUNTIME_NOT_FOUND,
    LOG_FILENAME,
    SCRIPT_FILENAME,
    job_name_for_task,
    normalize_arch,
    parse_extra_args,
    render_job_script,
    resource_directives,
)

# Directories that exist separately on every node, so a compute node cannot see
# what MedPerf writes there on the login node.
NODE_LOCAL_PREFIXES = ("/tmp", "/var/tmp", "/dev/shm")

STATUS_FILENAME = "medperf_status.json"

# How long to wait for the exit code file to become visible on the login node
# after the scheduler reports the job finished (shared filesystem caching).
EXIT_CODE_FILE_ATTEMPTS = 5
EXIT_CODE_FILE_DELAY = 2

# Seconds between reads of the job log while waiting for the next status check, so
# container output appears as it is written rather than once per poll interval.
LOG_STREAM_INTERVAL = 2

# A job's stdout is a file, not a terminal, so Python would block-buffer print()
# output and the log would arrive in bursts. Container configs can override this.
DEFAULT_CONTAINER_ENV = {"SINGULARITYENV_PYTHONUNBUFFERED": "1"}


def get_jobs_dir() -> str:
    base = config.slurm_jobs_dir or os.path.join(
        str(config.logs_storage), config.slurm_jobs_dirname
    )
    return os.path.abspath(os.path.expanduser(str(base)))


def create_job_dir(task: str) -> str:
    base = get_jobs_dir()
    os.makedirs(base, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    name = f"{timestamp}_{job_name_for_task(task)}_{generate_tmp_uid()}"
    job_dir = os.path.join(base, name)
    # 0700: the script may contain environment values meant for the container
    os.makedirs(job_dir, mode=0o700)
    return job_dir


def is_node_local(path: str) -> bool:
    real = os.path.realpath(path)
    return any(real == p or real.startswith(p + os.sep) for p in NODE_LOCAL_PREFIXES)


def describe_exit_code(rc: int) -> str:
    if rc == EXIT_PATH_NOT_VISIBLE:
        return (
            "could not start the container because a required path is not visible "
            "on the compute node. Make sure MedPerf storage, datasets and images are "
            "on a filesystem mounted on compute nodes"
        )
    if rc == EXIT_RUNTIME_NOT_FOUND:
        return (
            "could not find the container runtime on the compute node. Load it with "
            "--slurm-setup-commands (e.g. a 'module load' line) or check site access"
        )
    if rc == EXIT_ARCH_MISMATCH:
        return (
            "could not start the container because the image was built for a "
            "different CPU architecture than the compute node. Use an image built "
            "for the compute nodes' architecture"
        )
    if rc > 128:
        return f"container was killed by signal {rc - 128} (exit code {rc})"
    return f"container exited with code {rc}"


# Failure reasons for scheduler states that do not depend on the exit code.
STATE_FAILURE_REASONS = {
    "TIMEOUT": "reached its Slurm time limit and was stopped (see --slurm-time)",
    "OUT_OF_MEMORY": "ran out of memory and was killed (see --slurm-mem)",
    "PREEMPTED": "was preempted by the scheduler",
    "NODE_FAIL": "ended because of a compute node failure (NODE_FAIL)",
    "BOOT_FAIL": "ended because of a compute node failure (BOOT_FAIL)",
    "DEADLINE": "could not run before its deadline",
}


def evaluate_outcome(
    status: JobStatus, exit_code: Optional[int], cancelled_by_medperf: bool = False
) -> Optional[str]:
    # Returns a failure reason, or None on success. Success requires both the
    # scheduler state (what happened to the job) and the container's exit code
    # (written by the job script) to be good.
    state = status.state

    if state == commands.SUCCESS_STATE or (state is None and exit_code is not None):
        if exit_code is None:
            return (
                "completed but the workload's exit code was not recorded; the jobs "
                "directory may not be shared with compute nodes"
            )
        return None if exit_code == 0 else describe_exit_code(exit_code)

    if state == "FAILED":
        if exit_code is not None:
            return describe_exit_code(exit_code)
        detail = ""
        if status.exit_code is not None:
            detail = f" (job exit code {status.exit_code}, signal {status.signal})"
        return f"failed before the container finished{detail}"

    if state == "CANCELLED":
        if cancelled_by_medperf:
            return "was cancelled by MedPerf"
        return "was cancelled outside MedPerf (scancel, an administrator or Slurm)"

    return STATE_FAILURE_REASONS.get(state, f"ended in state {state}")


class SlurmJob:
    def __init__(self, job_dir: str, task: str):
        self.job_dir = job_dir
        self.task = task
        self.script_path = os.path.join(job_dir, SCRIPT_FILENAME)
        self.log_path = os.path.join(job_dir, LOG_FILENAME)
        self.exit_code_path = os.path.join(job_dir, EXIT_CODE_FILENAME)
        self.status_path = os.path.join(job_dir, STATUS_FILENAME)
        self.job: Optional[JobRef] = None
        self.started_at: Optional[float] = None
        self.cancel_requested = False
        self._wake = threading.Event()
        self._log_offset = 0
        self._log_partial = ""
        self._last_announced = None
        self._missing_since: Optional[float] = None
        self._seen = False

    def write_script(self, content: str):
        with open(self.script_path, "w") as f:
            f.write(content)
        # The job directory is already private (0700); keep the script private too.
        os.chmod(self.script_path, 0o600)

    def submit(self, extra_args: List[str] = None) -> JobRef:
        self.job = commands.submit(self.script_path, extra_args)
        logging.info(f"Submitted Slurm job {self.job} from {self.script_path}")
        return self.job

    def cancel(self):
        if self.job is None or self.cancel_requested:
            return
        self.cancel_requested = True
        logging.info(f"Cancelling Slurm job {self.job}")
        try:
            commands.cancel(self.job)
        except ExecutionError as e:
            logging.warning(f"Could not cancel Slurm job {self.job}: {e}")
            config.ui.print_warning(
                f"Could not cancel Slurm job {self.job}. Cancel it manually with: "
                f"scancel {self.job.job_id}"
            )
        self._wake.set()

    def killpg(self):
        # Same interface as medperf.utils.spawn_and_kill, used by the WebUI.
        self.cancel()

    def read_exit_code(self) -> Optional[int]:
        try:
            with open(self.exit_code_path) as f:
                return int(f.read().strip())
        except (OSError, ValueError):
            return None

    def read_exit_code_with_retry(self) -> Optional[int]:
        for attempt in range(EXIT_CODE_FILE_ATTEMPTS):
            exit_code = self.read_exit_code()
            if exit_code is not None or attempt == EXIT_CODE_FILE_ATTEMPTS - 1:
                return exit_code
            time.sleep(EXIT_CODE_FILE_DELAY)

    def stream_new_log_output(self, final: bool = False):
        try:
            with open(self.log_path, "r", errors="ignore") as f:
                f.seek(self._log_offset)
                chunk = f.read()
                self._log_offset = f.tell()
        except OSError:
            return
        text = self._log_partial + chunk
        lines = text.split("\n")
        self._log_partial = "" if final else lines.pop()
        for line in lines:
            if not line.strip():
                continue
            logging.debug(line)
            config.ui.print_subprocess_logs(
                f"{Fore.WHITE}{Style.DIM}{line.strip()}{Style.RESET_ALL}"
            )

    def read_log(self) -> Optional[str]:
        try:
            with open(self.log_path, "r", errors="ignore") as f:
                return f.read()
        except OSError:
            return None

    def _announce(self, status: JobStatus):
        key = (status.state, status.reason)
        if key == self._last_announced:
            return
        self._last_announced = key
        logging.info(
            f"Slurm job {self.job}: state={status.state} reason={status.reason} "
            f"node={status.node}"
        )
        if status.state == "PENDING":
            reason = f" (reason: {status.reason})" if status.reason else ""
            config.ui.text = f"Slurm job {self.job.job_id} is pending{reason}"
        elif status.state == "RUNNING":
            node = f" on {status.node}" if status.node else ""
            config.ui.text = f"Slurm job {self.job.job_id} is running{node}"
        else:
            config.ui.text = f"Slurm job {self.job.job_id}: {status.state}"

    def wait(self, timeout: int = None) -> JobStatus:
        # timeout limits running time only (not time pending in the queue), and is
        # separate from the scheduler's own --slurm-time limit.
        poll_interval = max(1, int(config.slurm_poll_interval))
        self._missing_since = None
        self._seen = False

        while True:
            status = commands.query_status(self.job)
            self.stream_new_log_output()

            if status.is_known:
                self._seen = True
                self._missing_since = None
                self._announce(status)
                if status.state == "RUNNING" and self.started_at is None:
                    self.started_at = time.monotonic()
                if status.is_terminal:
                    return status
            elif self.read_exit_code() is not None:
                # The job script finished but the scheduler no longer (or never)
                # reports the job, e.g. because accounting is disabled.
                return JobStatus(state=None, source="exit_code_file")
            else:
                self._check_missing_job(status)

            self._check_timeout(timeout)
            self._sleep_streaming_logs(poll_interval)

    def _sleep_streaming_logs(self, poll_interval: int):
        # Waits until the next status check while printing new log lines every
        # LOG_STREAM_INTERVAL seconds. Returns early if cancel() wakes it.
        deadline = time.monotonic() + poll_interval
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return
            if self._wake.wait(min(LOG_STREAM_INTERVAL, remaining)):
                self._wake.clear()
                return
            self.stream_new_log_output()

    def _check_missing_job(self, status: JobStatus):
        # A job can be briefly invisible: between leaving squeue and appearing in
        # sacct, or while the controller is unresponsive.
        grace = int(config.slurm_accounting_grace)
        now = time.monotonic()
        if self._missing_since is None:
            self._missing_since = now
        if now - self._missing_since <= grace:
            return
        if self._seen:
            what = "is no longer reported by squeue or sacct"
        else:
            what = "is unknown to squeue and sacct"
        error = f" Last error: {status.error}." if status.error else ""
        raise ExecutionError(
            f"Slurm job {self.job} {what} and wrote no exit code after {grace} "
            f"seconds.{error} Check it with: sacct -j {self.job.job_id}"
        )

    def _check_timeout(self, timeout: Optional[int]):
        if not timeout or self.started_at is None:
            return
        if time.monotonic() - self.started_at > timeout:
            raise ExecutionError(
                f"Slurm job {self.job} exceeded the MedPerf timeout of "
                f"{timeout} seconds"
            )

    def save_status(self, status: JobStatus, exit_code: Optional[int], failure):
        record = {
            "job_id": self.job.job_id if self.job else None,
            "cluster": self.job.cluster if self.job else None,
            "task": self.task,
            "state": status.state,
            "state_source": status.source,
            "node": status.node,
            "exit_code": exit_code,
            "failure": failure,
        }
        try:
            with open(self.status_path, "w") as f:
                json.dump(record, f, indent=2)
        except OSError as e:
            logging.warning(f"Could not write {self.status_path}: {e}")


def expected_node_arch() -> str:
    # Assumed to be this (login) node's unless --slurm-node-arch is given
    return normalize_arch(config.slurm_node_arch or platform.machine())


def check_image_architecture(image: str, image_arch: Optional[str]):
    image_arch = normalize_arch(image_arch)
    node_arch = expected_node_arch()
    if image_arch is None or node_arch is None:
        logging.debug(f"Skipping architecture check: {image_arch=} {node_arch=}")
        return
    if image_arch == node_arch:
        return
    source = "--slurm-node-arch" if config.slurm_node_arch else "this login node"
    raise InvalidArgumentError(
        f"The container image {image} is built for {image_arch}, but the compute "
        f"nodes are {node_arch} (from {source}), so it cannot run there. Use an image "
        f"built for {node_arch}. If the compute nodes' architecture differs from the "
        "login node's, set it with --slurm-node-arch."
    )


def _warn_about_configuration(job_dir: str, paths: List[str], gpu_enabled: bool):
    ui = config.ui
    for path in [job_dir, *paths]:
        if is_node_local(path):
            ui.print_warning(
                f"{path} is on node-local storage and will not be visible from the "
                "compute node. Move MedPerf storage and the Slurm jobs directory to "
                "a shared filesystem."
            )

    extra = config.slurm_extra_args or ""
    gpus_requested = (config.slurm_gres and "gpu" in config.slurm_gres) or (
        "--gres" in extra or "--gpus" in extra or "-G" in extra.split()
    )
    if gpu_enabled and not gpus_requested:
        ui.print_warning(
            "The container is configured to use GPUs but no GPUs were requested "
            "from Slurm (--slurm-gres). The cluster's default GPU allocation applies."
        )
    if not gpu_enabled and config.slurm_gres and "gpu" in config.slurm_gres:
        ui.print_warning(
            "GPUs are requested from Slurm but the container has no GPU access. "
            "Pass --gpus=all to give the container the job's GPUs."
        )


def run_in_slurm(
    command: List[str],
    timeout: int = None,
    output_logs: str = None,
    task: str = None,
    env: Dict[str, str] = None,
    paths_to_check: List[str] = None,
    gpu_enabled: bool = False,
    image: str = None,
    image_arch: str = None,
) -> str:
    commands.check_slurm_available()
    check_image_architecture(image, image_arch)
    directives = resource_directives(
        partition=config.slurm_partition,
        account=config.slurm_account,
        time=config.slurm_time,
        cpus_per_task=config.slurm_cpus_per_task,
        mem=config.slurm_mem,
        gres=config.slurm_gres,
    )
    extra_args = parse_extra_args(config.slurm_extra_args)
    paths_to_check = paths_to_check or []
    env = {**DEFAULT_CONTAINER_ENV, **(env or {})}

    job_dir = create_job_dir(task)
    _warn_about_configuration(job_dir, paths_to_check, gpu_enabled)

    job = SlurmJob(job_dir, task)
    job.write_script(
        render_job_script(
            command,
            job_dir,
            task,
            env=env,
            paths_to_check=paths_to_check,
            forward_gpu_visibility=gpu_enabled,
            setup_commands=config.slurm_setup_commands,
            directives=directives,
            image_arch=image_arch,
        )
    )
    job.submit(extra_args)
    config.ui.print(f"> Submitted Slurm job {job.job} for task '{task}'")
    config.ui.print(f"> Job log: {job.log_path}")

    if task:
        config.running_containers[task] = job
    try:
        status = job.wait(timeout)
    except BaseException as e:
        # Covers Ctrl+C, MedPerf timeouts and monitoring errors: never leave the
        # job running after MedPerf stops tracking it.
        logging.info(f"Stopping Slurm job {job.job} because of: {e!r}")
        job.cancel()
        raise
    finally:
        if task:
            config.running_containers.pop(task, None)

    exit_code = job.read_exit_code()
    if exit_code is None and status.state == commands.SUCCESS_STATE:
        exit_code = job.read_exit_code_with_retry()
    job.stream_new_log_output(final=True)

    log_text = job.read_log()
    if output_logs is not None:
        with open(output_logs, "w") as f:
            f.write(log_text or "")

    failure = evaluate_outcome(status, exit_code, job.cancel_requested)
    if failure and log_text is None:
        failure += (
            f". No job log was written to {job.log_path}: Slurm could not open it, "
            "which usually means the jobs directory is not shared with compute nodes"
        )
    elif failure and "exec format error" in log_text.lower():
        # Backstop for images whose architecture could not be read beforehand.
        failure += (
            ". The log shows 'exec format error': the image was built for a "
            "different CPU architecture than the compute node"
        )
    job.save_status(status, exit_code, failure)

    if failure:
        raise ExecutionError(f"Slurm job {job.job} {failure}. Log: {job.log_path}")
    logging.info(f"Slurm job {job.job} completed successfully")
    return log_text or ""
