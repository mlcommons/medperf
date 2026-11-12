import re
import shlex
from datetime import datetime
from typing import Dict, List, Optional

from medperf.exceptions import InvalidArgumentError

# Exit codes for failures before the container runs, in a range rarely used by
# applications so they can be told apart.
EXIT_PATH_NOT_VISIBLE = 97
EXIT_RUNTIME_NOT_FOUND = 98
EXIT_ARCH_MISMATCH = 99

EXIT_CODE_FILENAME = "exit_code"
SCRIPT_FILENAME = "job.sh"
LOG_FILENAME = "job.log"
LOG_PREFIX = "MEDPERF-SLURM:"

# Formats accepted by sbatch --time: "minutes", "minutes:seconds",
# "hours:minutes:seconds", "days-hours", "days-hours:minutes",
# "days-hours:minutes:seconds"
_TIME_RE = re.compile(r"^(\d+|\d+:\d{1,2}|\d+:\d{1,2}:\d{1,2}|\d+-\d+(:\d{1,2}){0,2})$")
_MEM_RE = re.compile(r"^\d+[KMGT]?$", re.IGNORECASE)
_NAME_RE = re.compile(r"^[A-Za-z0-9_.,\-]+$")
_GRES_RE = re.compile(r"^[A-Za-z0-9_.,:\-]+$")
_ENV_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_ARCH_RE = re.compile(r"^[A-Za-z0-9_]+$")
# Slurm expands %j, %x... in --output, and #SBATCH lines are split on whitespace.
_JOB_DIR_RE = re.compile(r"^/[^\s%]+$")

# sbatch options that MedPerf controls itself and must not be overridden.
_RESERVED_OPTIONS = {
    "--output",
    "--error",
    "--job-name",
    "--parsable",
    "--wrap",
    "--chdir",
    "-o",
    "-e",
    "-J",
    "-D",
}


def normalize_arch(arch: Optional[str]) -> Optional[str]:
    # uname -m names (x86_64, aarch64, ...) to image metadata names (amd64, arm64, ...)
    if not arch:
        return None
    arch = arch.strip().lower()
    if arch in ("x86_64", "amd64"):
        return "amd64"
    if arch in ("aarch64", "arm64"):
        return "arm64"
    if re.fullmatch(r"i[3-6]86|386", arch):
        return "386"
    if arch.startswith("armv") or arch == "arm":
        return "arm"
    return arch


# The same mapping as normalize_arch, in shell, for the compute node's `uname -m`.
_SHELL_NORMALIZE_ARCH = """case "$node_arch" in
    x86_64|amd64) node_arch=amd64 ;;
    aarch64|arm64) node_arch=arm64 ;;
    i[3-6]86) node_arch=386 ;;
    armv*) node_arch=arm ;;
esac"""


def validate_resources(
    partition: Optional[str] = None,
    account: Optional[str] = None,
    time: Optional[str] = None,
    cpus_per_task: Optional[int] = None,
    mem: Optional[str] = None,
    gres: Optional[str] = None,
):
    # Values are written into #SBATCH lines, so whitespace or newlines must not
    # get through.
    if partition is not None and not _NAME_RE.match(str(partition)):
        raise InvalidArgumentError(f"Invalid Slurm partition: {partition!r}")
    if account is not None and not _NAME_RE.match(str(account)):
        raise InvalidArgumentError(f"Invalid Slurm account: {account!r}")
    if time is not None and not _TIME_RE.match(str(time)):
        raise InvalidArgumentError(
            f"Invalid Slurm time limit: {time!r}. Use a Slurm time format such as "
            "'90' (minutes), '02:00:00' or '1-12:00:00'."
        )
    if cpus_per_task is not None:
        if isinstance(cpus_per_task, bool) or int(cpus_per_task) < 1:
            raise InvalidArgumentError(
                f"Invalid Slurm cpus per task: {cpus_per_task!r}"
            )
    if mem is not None and not _MEM_RE.match(str(mem)):
        raise InvalidArgumentError(
            f"Invalid Slurm memory: {mem!r}. Use e.g. '64G', '512M' or '0'."
        )
    if gres is not None and not _GRES_RE.match(str(gres)):
        raise InvalidArgumentError(f"Invalid Slurm gres: {gres!r}. Use e.g. 'gpu:4'.")


def parse_extra_args(extra_args: Optional[str]) -> List[str]:
    if not extra_args:
        return []
    try:
        args = shlex.split(extra_args)
    except ValueError as e:
        raise InvalidArgumentError(f"Invalid Slurm extra args {extra_args!r}: {e}")
    for arg in args:
        option = arg.split("=", 1)[0]
        if option in _RESERVED_OPTIONS:
            raise InvalidArgumentError(
                f"The sbatch option {option} is managed by MedPerf and cannot be "
                "passed through slurm_extra_args."
            )
    return args


def resource_directives(
    partition: Optional[str] = None,
    account: Optional[str] = None,
    time: Optional[str] = None,
    cpus_per_task: Optional[int] = None,
    mem: Optional[str] = None,
    gres: Optional[str] = None,
) -> List[str]:
    # Unset values are omitted so the cluster's defaults apply
    validate_resources(partition, account, time, cpus_per_task, mem, gres)
    # A MedPerf container is a single process on a single node.
    directives = ["--nodes=1", "--ntasks=1"]
    if partition is not None:
        directives.append(f"--partition={partition}")
    if account is not None:
        directives.append(f"--account={account}")
    if time is not None:
        directives.append(f"--time={time}")
    if cpus_per_task is not None:
        directives.append(f"--cpus-per-task={int(cpus_per_task)}")
    if mem is not None:
        directives.append(f"--mem={mem}")
    if gres is not None:
        directives.append(f"--gres={gres}")
    return [f"#SBATCH {d}" for d in directives]


def job_name_for_task(task: str) -> str:
    safe_task = re.sub(r"[^A-Za-z0-9_.\-]", "_", task or "task")
    return f"medperf-{safe_task}"


def _bind_sources(command: List[str]) -> List[str]:
    sources = []
    for flag, value in zip(command, command[1:]):
        if flag in ("--bind", "-B"):
            sources.append(value.split(":", 1)[0])
    return sources


def _validate_script_inputs(job_dir: str, env: Dict[str, str], image_arch):
    if not _JOB_DIR_RE.match(job_dir):
        raise InvalidArgumentError(
            f"Slurm jobs directory {job_dir!r} must be an absolute path without "
            "whitespace or '%' characters."
        )
    for key in env:
        if not _ENV_NAME_RE.match(key):
            raise InvalidArgumentError(f"Invalid environment variable name: {key!r}")
    if image_arch is None:
        return None
    image_arch = normalize_arch(image_arch)
    if not _ARCH_RE.match(image_arch):
        raise InvalidArgumentError(f"Invalid image architecture: {image_arch!r}")
    return image_arch


def _arch_check_lines(image_arch: str) -> List[str]:
    return [
        "",
        "# The image only runs on compute nodes with the CPU architecture it was",
        "# built for.",
        "node_arch=$(uname -m)",
        _SHELL_NORMALIZE_ARCH,
        f'if [ "$node_arch" != {image_arch} ]; then',
        f'    echo "{LOG_PREFIX} the container image is built for {image_arch} but '
        'this compute node is $(uname -m)" >&2',
        f"    medperf_finish {EXIT_ARCH_MISMATCH}",
        "fi",
    ]


def render_job_script(
    command: List[str],
    job_dir: str,
    task: str,
    env: Dict[str, str] = None,
    paths_to_check: List[str] = None,
    forward_gpu_visibility: bool = False,
    setup_commands: Optional[str] = None,
    directives: List[str] = None,
    image_arch: Optional[str] = None,
) -> str:
    """Renders the batch script that runs `command` on a compute node.

    Args:
        command (List[str]): the container command MedPerf would run locally.
        job_dir (str): absolute directory, shared with compute nodes.
        task (str): MedPerf task name.
        env (dict): variables to export before running the command.
        paths_to_check (List[str]): host paths that must be visible on the node.
            Bind sources of `command` are always checked.
        forward_gpu_visibility (bool): pass Slurm's CUDA_VISIBLE_DEVICES to the container.
        setup_commands (str): shell lines run before the container, inserted verbatim.
        directives (List[str]): #SBATCH resource lines.
        image_arch (str): architecture the image was built for, checked on the node.

    Returns:
        str: the script
    """
    q = shlex.quote
    env = env or {}
    image_arch = _validate_script_inputs(job_dir, env, image_arch)
    checks = list(dict.fromkeys([*(paths_to_check or []), *_bind_sources(command)]))
    exit_code_file = f"{job_dir}/{EXIT_CODE_FILENAME}"
    executable = command[0]

    lines = [
        "#!/bin/bash",
        f"# Generated by MedPerf on {datetime.now().isoformat(timespec='seconds')}"
        f" for task '{task}'.",
        "# It can be resubmitted manually for debugging: sbatch job.sh",
        f"#SBATCH --job-name={job_name_for_task(task)}",
        f"#SBATCH --output={job_dir}/{LOG_FILENAME}",
        f"#SBATCH --chdir={job_dir}",
        # A requeued job would rerun the workload under the same job ID while
        # MedPerf may already have reported the first attempt as failed.
        "#SBATCH --no-requeue",
        *(directives or []),
        "",
        f"EXIT_CODE_FILE={q(exit_code_file)}",
        "",
        "medperf_finish() {",
        '    echo "$1" > "$EXIT_CODE_FILE.tmp" && mv "$EXIT_CODE_FILE.tmp" "$EXIT_CODE_FILE"',
        '    exit "$1"',
        "}",
        "",
        f'echo "{LOG_PREFIX} job ${{SLURM_JOB_ID:-?}} started on $(hostname) at $(date)"',
    ]

    if setup_commands:
        lines += ["", "# --- user setup commands ---", setup_commands.rstrip(), "# ---"]

    if checks:
        lines += [
            "",
            "# Paths that MedPerf prepared on the login node must be visible here.",
            f"for path in {' '.join(q(p) for p in checks)}; do",
            '    if [ ! -e "$path" ]; then',
            f'        echo "{LOG_PREFIX} path not visible on compute node: $path" >&2',
            f"        medperf_finish {EXIT_PATH_NOT_VISIBLE}",
            "    fi",
            "done",
        ]

    lines += [
        "",
        f"if ! command -v {q(executable)} > /dev/null 2>&1; then",
        f'    echo "{LOG_PREFIX} container runtime not found on compute node: "{q(executable)} >&2',
        f"    medperf_finish {EXIT_RUNTIME_NOT_FOUND}",
        "fi",
    ]

    if image_arch:
        lines += _arch_check_lines(image_arch)

    if env:
        lines += ["", "# Environment passed into the container."]
        lines += [f"export {key}={q(value)}" for key, value in sorted(env.items())]

    if forward_gpu_visibility:
        lines += [
            "",
            "# The container starts with a clean environment; give it the GPUs",
            "# Slurm assigned to this job.",
            'if [ -n "${CUDA_VISIBLE_DEVICES:-}" ]; then',
            '    export SINGULARITYENV_CUDA_VISIBLE_DEVICES="$CUDA_VISIBLE_DEVICES"',
            "fi",
        ]

    lines += [
        "",
        f'echo "{LOG_PREFIX} starting container"',
        " ".join(q(arg) for arg in command),
        "rc=$?",
        f'echo "{LOG_PREFIX} container exited with code $rc at $(date)"',
        'medperf_finish "$rc"',
        "",
    ]
    return "\n".join(lines)
