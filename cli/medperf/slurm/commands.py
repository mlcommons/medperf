import logging
import os
import re
import shutil
import subprocess
from typing import Dict, List, Optional

from medperf import config
from medperf.exceptions import SlurmCommandError, SlurmCommandNotFound

# Job states in which the job is finished and will not change anymore.
# https://slurm.schedmd.com/job_state_codes.html
TERMINAL_STATES = {
    "COMPLETED",
    "FAILED",
    "CANCELLED",
    "TIMEOUT",
    "OUT_OF_MEMORY",
    "NODE_FAIL",
    "PREEMPTED",
    "BOOT_FAIL",
    "DEADLINE",
    "REVOKED",
    "SPECIAL_EXIT",
}

SUCCESS_STATE = "COMPLETED"

# The container's environment is written into job.sh. Leftover container variables in
# medperf's own environment (e.g. from an earlier task) must not reach the job through
# sbatch's default --export=ALL.
CONTAINER_ENV_PREFIXES = ("SINGULARITYENV_", "APPTAINERENV_")

# Short state codes (squeue %t) mapped to long names, in case a site's squeue
# prints short codes.
SHORT_STATES = {
    "BF": "BOOT_FAIL",
    "CA": "CANCELLED",
    "CD": "COMPLETED",
    "CF": "CONFIGURING",
    "CG": "COMPLETING",
    "DL": "DEADLINE",
    "F": "FAILED",
    "NF": "NODE_FAIL",
    "OOM": "OUT_OF_MEMORY",
    "PD": "PENDING",
    "PR": "PREEMPTED",
    "R": "RUNNING",
    "RD": "RESV_DEL_HOLD",
    "RF": "REQUEUE_FED",
    "RH": "REQUEUE_HOLD",
    "RQ": "REQUEUED",
    "RS": "RESIZING",
    "RV": "REVOKED",
    "SI": "SIGNALING",
    "SE": "SPECIAL_EXIT",
    "SO": "STAGE_OUT",
    "ST": "STOPPED",
    "S": "SUSPENDED",
    "TO": "TIMEOUT",
}


class JobRef:
    def __init__(self, job_id: str, cluster: Optional[str] = None):
        self.job_id = job_id
        # Only set on multi-cluster setups, where sbatch prints "<jobid>;<cluster>"
        self.cluster = cluster

    def cluster_args(self) -> List[str]:
        return [f"--clusters={self.cluster}"] if self.cluster else []

    def __str__(self):
        return f"{self.job_id};{self.cluster}" if self.cluster else self.job_id


class JobStatus:
    def __init__(
        self,
        state: Optional[str],
        reason: Optional[str] = None,
        exit_code: Optional[int] = None,
        signal: Optional[int] = None,
        node: Optional[str] = None,
        source: Optional[str] = None,
        error: Optional[str] = None,
    ):
        # state is None when the scheduler has no record of the job (yet, or anymore)
        self.state = state
        self.reason = reason
        # exit_code and signal are only known from accounting (sacct)
        self.exit_code = exit_code
        self.signal = signal
        self.node = node
        self.source = source
        self.error = error

    @property
    def is_known(self) -> bool:
        return self.state is not None

    @property
    def is_terminal(self) -> bool:
        return self.state in TERMINAL_STATES


def check_slurm_available():
    if shutil.which("sbatch") is None:
        raise SlurmCommandNotFound(
            "The 'sbatch' command was not found. The slurm launcher must be used "
            "on a Slurm submit host (e.g. a cluster login node). "
            "Use '--launcher local' to run containers locally."
        )


def _run(
    args: List[str], timeout: int = None, env: Dict[str, str] = None
) -> subprocess.CompletedProcess:
    if timeout is None:
        timeout = config.slurm_command_timeout
    logging.debug(f"Running slurm command: {args}")
    try:
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=timeout, check=False, env=env
        )
    except FileNotFoundError:
        raise SlurmCommandNotFound(f"Slurm command '{args[0]}' was not found.")
    except subprocess.TimeoutExpired:
        raise SlurmCommandError(
            f"Slurm command '{args[0]}' did not respond within {timeout} seconds."
        )
    logging.debug(
        f"{args[0]} exited {result.returncode}. "
        f"stdout: {result.stdout.strip()!r} stderr: {result.stderr.strip()!r}"
    )
    return result


def parse_sbatch_output(stdout: str) -> JobRef:
    # Output is "<jobid>" or "<jobid>;<cluster>". Some sites' submit plugins print
    # extra lines, so the last matching line wins.
    for line in reversed(stdout.strip().splitlines()):
        match = re.fullmatch(r"\s*(\d+)(?:;(\S+))?\s*", line)
        if match:
            return JobRef(job_id=match.group(1), cluster=match.group(2))
    raise SlurmCommandError(f"Could not parse a job ID from sbatch output: {stdout!r}")


def submission_env() -> Dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(CONTAINER_ENV_PREFIXES)
    }


def submit(script_path: str, extra_args: List[str] = None) -> JobRef:
    args = ["sbatch", "--parsable", *(extra_args or []), script_path]
    result = _run(args, env=submission_env())
    if result.returncode != 0:
        # sbatch explains rejections (invalid account, partition, time limit...)
        # on stderr; pass that message on to the user verbatim.
        message = result.stderr.strip() or result.stdout.strip()
        raise SlurmCommandError(f"Slurm rejected the job submission: {message}")
    return parse_sbatch_output(result.stdout)


def normalize_state(raw: str) -> Optional[str]:
    # e.g. "CANCELLED by 1234" -> "CANCELLED", "CD" -> "COMPLETED"
    if not raw or not raw.strip():
        return None
    state = raw.strip().split()[0].rstrip("+").upper()
    return SHORT_STATES.get(state, state)


def parse_exit_code(raw: str):
    # sacct prints ExitCode as "<exit status>:<signal>"
    match = re.fullmatch(r"\s*(\d+):(\d+)\s*", raw or "")
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))


def parse_squeue_output(stdout: str) -> JobStatus:
    lines = [line for line in stdout.strip().splitlines() if line.strip()]
    if not lines:
        return JobStatus(state=None, source="squeue")
    state, _, rest = lines[0].partition("|")
    reason, _, node = rest.partition("|")
    reason = reason.strip()
    node = node.strip()
    return JobStatus(
        state=normalize_state(state),
        reason=reason if reason and reason != "None" else None,
        node=node or None,
        source="squeue",
    )


def parse_sacct_output(stdout: str, job_id: str) -> JobStatus:
    for line in reversed(stdout.strip().splitlines()):
        fields = line.split("|")
        if len(fields) < 3 or fields[0].strip() != job_id:
            continue
        exit_code, signal = parse_exit_code(fields[2])
        node = fields[3].strip() if len(fields) > 3 else ""
        return JobStatus(
            state=normalize_state(fields[1]),
            exit_code=exit_code,
            signal=signal,
            node=node if node and node != "None assigned" else None,
            source="sacct",
        )
    return JobStatus(state=None, source="sacct")


def query_squeue(job: JobRef) -> JobStatus:
    args = [
        "squeue",
        *job.cluster_args(),
        "--noheader",
        f"--jobs={job.job_id}",
        "--states=all",
        "--format=%T|%r|%N",
    ]
    result = _run(args)
    if result.returncode != 0:
        if "invalid job id" in result.stderr.lower():
            # Finished jobs are dropped from squeue after a while (MinJobAge)
            return JobStatus(state=None, source="squeue")
        return JobStatus(
            state=None, source="squeue", error=result.stderr.strip() or "squeue failed"
        )
    return parse_squeue_output(result.stdout)


def query_sacct(job: JobRef) -> JobStatus:
    if shutil.which("sacct") is None:
        return JobStatus(state=None, source="sacct", error="sacct not available")
    args = [
        "sacct",
        *job.cluster_args(),
        "--noheader",
        "--parsable2",
        "--allocations",
        f"--jobs={job.job_id}",
        "--format=JobID,State,ExitCode,NodeList",
    ]
    result = _run(args)
    if result.returncode != 0:
        return JobStatus(
            state=None, source="sacct", error=result.stderr.strip() or "sacct failed"
        )
    return parse_sacct_output(result.stdout, job.job_id)


def query_status(job: JobRef) -> JobStatus:
    # squeue is fresh but forgets finished jobs; sacct keeps them (with exit codes)
    # but may lag behind or be disabled.
    status = query_squeue(job)
    if status.is_known and not status.is_terminal:
        return status

    accounting = query_sacct(job)
    if accounting.is_known:
        if status.is_known and not accounting.is_terminal:
            # accounting is lagging behind the controller
            return status
        if status.reason and not accounting.reason:
            accounting.reason = status.reason
        return accounting

    if status.is_known:
        return status
    errors = "; ".join(e for e in [status.error, accounting.error] if e)
    return JobStatus(state=None, error=errors or None)


def cancel(job: JobRef) -> bool:
    result = _run(["scancel", *job.cluster_args(), job.job_id])
    if result.returncode != 0:
        # e.g. the job had already finished
        logging.warning(f"scancel {job} failed: {result.stderr.strip()}")
        return False
    return True
