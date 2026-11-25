# End-to-end tests of the Slurm launcher against a fake Slurm (see fake_slurm.py):
# real job scripts, processes and files; only the scheduler is simulated. They do
# not prove anything about a real Slurm cluster.
# The real-container tests also need apptainer/singularity and a SIF image with
# python3:  MEDPERF_SLURM_TEST_SIF=/path/to/image.sif pytest slurm

import os
import shutil
import subprocess
import sys
import threading
import time

import pytest

from medperf import config
from medperf.containers.runners.singularity_utils import (
    craft_singularity_run_command,
    get_sif_architecture,
)
from medperf.exceptions import ExecutionError, SlurmCommandError
from medperf.slurm import launcher, run_in_slurm
from medperf.slurm.job_script import render_job_script, resource_directives
from medperf.ui.cli import CLI

FAKE_SLURM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fake_slurm.py")
SLURM_COMMANDS = ["sbatch", "squeue", "sacct", "scancel"]

pytestmark = pytest.mark.skipif(
    sys.platform == "win32" or shutil.which("bash") is None, reason="needs bash"
)


@pytest.fixture(autouse=True)
def package_init(tmp_path, mocker, monkeypatch):
    # Overrides conftest's package_init, which puts every test on a fake filesystem
    saved = {k: getattr(config, k) for k in dir(config) if not k.startswith("__")}

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for command in SLURM_COMMANDS:
        wrapper = bin_dir / command
        wrapper.write_text(
            f'#!/bin/sh\nexec "{sys.executable}" "{FAKE_SLURM}" {command} "$@"\n'
        )
        wrapper.chmod(0o755)
    state = tmp_path / "slurm_state"
    state.mkdir()
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_SLURM_STATE", str(state))
    for var in ["FAKE_SLURM_REJECT", "FAKE_SLURM_NO_SACCT", "FAKE_SLURM_PURGE"]:
        monkeypatch.delenv(var, raising=False)

    config.ui = mocker.create_autospec(spec=CLI)
    config.launcher = "slurm"
    config.slurm_jobs_dir = str(tmp_path / "jobs")
    config.slurm_poll_interval = 1
    config.slurm_accounting_grace = 10
    config.running_containers = {}
    yield
    for key, value in saved.items():
        setattr(config, key, value)


def job_dirs():
    if not os.path.isdir(config.slurm_jobs_dir):
        return []
    return [
        os.path.join(config.slurm_jobs_dir, d) for d in os.listdir(config.slurm_jobs_dir)
    ]


def test_generated_job_script_is_valid_bash(tmp_path):
    # Arrange
    script = render_job_script(
        ["apptainer", "run", "--bind", "/a b:/x", "/img.sif"],
        str(tmp_path),
        "infer",
        env={"SINGULARITYENV_A": "x'y\"z $HOME"},
        paths_to_check=["/img.sif"],
        forward_gpu_visibility=True,
        setup_commands="echo setup",
        directives=resource_directives(time="10", partition="booster"),
    )

    # Act: syntax check only
    result = subprocess.run(["bash", "-n"], input=script, capture_output=True, text=True)

    # Assert
    assert result.returncode == 0, result.stderr


def test_successful_job_streams_output_and_writes_logs(tmp_path):
    # Arrange
    output_logs = tmp_path / "model.log"

    # Act
    log = run_in_slurm(
        ["bash", "-c", "echo working; echo done"],
        output_logs=str(output_logs),
        task="infer",
    )

    # Assert
    assert "working\ndone" in log
    assert output_logs.read_text() == log
    assert "MEDPERF-SLURM: container exited with code 0" in log
    printed = [c.args[0] for c in config.ui.print_subprocess_logs.call_args_list]
    assert any("working" in p for p in printed)
    assert "infer" not in config.running_containers


def test_output_is_shown_while_the_job_runs_not_once_per_poll():
    # Status is checked only every 10 s, but the log is read every second, so the
    # first line must reach the UI while the job is still running.
    config.slurm_poll_interval = 10
    shown_while_running = []

    def record(line):
        if "early" in line:
            [job_dir] = job_dirs()
            finished = os.path.exists(os.path.join(job_dir, "exit_code"))
            shown_while_running.append(not finished)

    config.ui.print_subprocess_logs.side_effect = record

    # Act
    # (the first line comes after the first status check, so only the per-second
    # log reads can show it before the job ends)
    run_in_slurm(["bash", "-c", "sleep 2; echo early; sleep 4; echo late"], task="infer")

    # Assert
    assert shown_while_running == [True]


def test_arguments_reach_the_workload_unchanged(tmp_path):
    # Arrange: arguments a shell would otherwise interpret
    marker = tmp_path / "injected"
    args = ["a b", f"$(touch {marker})", "it's", "`id`", ";", "*"]

    # Act
    log = run_in_slurm(["printf", "[%s]\n", *args], task="infer")

    # Assert
    for arg in args:
        assert f"[{arg}]" in log
    assert not marker.exists()


def test_environment_is_exported_by_the_job_script(monkeypatch):
    # Arrange: make sure the value cannot leak in from the submitting process
    monkeypatch.delenv("SINGULARITYENV_MSG", raising=False)

    # Act
    log = run_in_slurm(
        ["bash", "-c", 'echo "msg=$SINGULARITYENV_MSG"'],
        task="infer",
        env={"SINGULARITYENV_MSG": "hello $USER; it's fine"},
    )

    # Assert
    assert "msg=hello $USER; it's fine" in log


def test_leftover_container_env_does_not_reach_the_job(monkeypatch):
    # Arrange: a container variable left in medperf's environment by an earlier
    # task. The fake sbatch, like Slurm's default --export=ALL, passes its own
    # environment to the job.
    monkeypatch.setenv("SINGULARITYENV_LEFTOVER", "stale")

    # Act
    log = run_in_slurm(
        ["bash", "-c", 'echo "leftover=${SINGULARITYENV_LEFTOVER:-none} '
         'current=$SINGULARITYENV_CURRENT"'],
        task="evaluate",
        env={"SINGULARITYENV_CURRENT": "this-task"},
    )

    # Assert
    assert "leftover=none current=this-task" in log


def test_nonzero_exit_code_fails_the_task():
    # Act & Assert
    with pytest.raises(ExecutionError, match="container exited with code 3"):
        run_in_slurm(["bash", "-c", "echo failing; exit 3"], task="evaluate")
    [job_dir] = job_dirs()
    assert open(os.path.join(job_dir, "exit_code")).read().strip() == "3"


def test_submission_rejection_is_reported(monkeypatch):
    monkeypatch.setenv("FAKE_SLURM_REJECT", "1")
    with pytest.raises(SlurmCommandError, match="Invalid account"):
        run_in_slurm(["true"], task="infer")


def test_path_not_visible_on_compute_node_is_explained(tmp_path):
    with pytest.raises(ExecutionError, match="not visible on the compute node"):
        run_in_slurm(
            ["true"], task="infer", paths_to_check=[str(tmp_path / "missing.sif")]
        )


def test_missing_runtime_on_compute_node_is_explained():
    with pytest.raises(ExecutionError, match="container runtime"):
        run_in_slurm(["definitely-not-a-runtime-xyz", "run"], task="infer")


def test_architecture_mismatch_on_compute_node_is_explained():
    # The login-side check passes (node arch configured as s390x), but the
    # "compute node" this fake Slurm runs on is not s390x.
    config.slurm_node_arch = "s390x"
    with pytest.raises(ExecutionError, match="different CPU architecture"):
        run_in_slurm(["true"], task="infer", image="/i.sif", image_arch="s390x")
    [job_dir] = job_dirs()
    log = open(os.path.join(job_dir, "job.log")).read()
    assert "image is built for s390x but this compute node is" in log


def test_success_without_accounting_uses_exit_code_file(monkeypatch):
    # squeue forgets the job as soon as it ends and sacct is disabled
    monkeypatch.setenv("FAKE_SLURM_NO_SACCT", "1")
    monkeypatch.setenv("FAKE_SLURM_PURGE", "1")
    log = run_in_slurm(["bash", "-c", "sleep 1; echo ok"], task="infer")
    assert "ok" in log


def test_failure_without_accounting_uses_exit_code_file(monkeypatch):
    monkeypatch.setenv("FAKE_SLURM_NO_SACCT", "1")
    monkeypatch.setenv("FAKE_SLURM_PURGE", "1")
    with pytest.raises(ExecutionError, match="exited with code 4"):
        run_in_slurm(["bash", "-c", "sleep 1; exit 4"], task="infer")


def test_cluster_suffix_from_sbatch(monkeypatch):
    monkeypatch.setenv("FAKE_SLURM_CLUSTER", "jupiter")
    assert "ok" in run_in_slurm(["echo", "ok"], task="infer")


def wait_for_running_job(task, timeout=20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = config.running_containers.get(task)
        if job is not None and job.started_at is not None:
            return job
        time.sleep(0.2)
    raise AssertionError("job did not start")


def test_stop_from_webui_cancels_the_slurm_job(tmp_path):
    # Arrange: the WebUI stops tasks via config.running_containers[task].killpg()
    pid_file = tmp_path / "workload.pid"
    errors = []

    def run():
        try:
            run_in_slurm(
                ["bash", "-c", f"echo $$ > {pid_file}; exec sleep 60"], task="infer"
            )
        except ExecutionError as e:
            errors.append(e)

    thread = threading.Thread(target=run)
    thread.start()

    # Act
    wait_for_running_job("infer").killpg()
    thread.join(timeout=30)

    # Assert
    assert not thread.is_alive()
    assert errors and "cancelled by MedPerf" in str(errors[0])
    pid = int(pid_file.read_text())
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)


def test_medperf_timeout_cancels_the_job(tmp_path):
    # Arrange
    pid_file = tmp_path / "workload.pid"

    # Act & Assert
    with pytest.raises(ExecutionError, match="MedPerf timeout of 2 seconds"):
        run_in_slurm(
            ["bash", "-c", f"echo $$ > {pid_file}; exec sleep 60"],
            task="infer",
            timeout=2,
        )
    time.sleep(1)
    with pytest.raises(ProcessLookupError):
        os.kill(int(pid_file.read_text()), 0)


def container_runtime():
    for name in ["apptainer", "singularity"]:
        if shutil.which(name):
            return name
    return None


@pytest.mark.skipif(
    not os.environ.get("MEDPERF_SLURM_TEST_SIF") or container_runtime() is None,
    reason="set MEDPERF_SLURM_TEST_SIF and install apptainer/singularity",
)
def test_real_container_through_fake_slurm(tmp_path, monkeypatch):
    # Arrange: the same command construction the SingularityRunner uses
    data = tmp_path / "data"
    data.mkdir()
    (data / "input.txt").write_text("input-data\n")
    out = tmp_path / "out"
    out.mkdir()
    env = {}
    command = craft_singularity_run_command(
        {
            "remove_container": True,
            "user": f"{os.getuid()}:{os.getgid()}",
            "image": os.environ["MEDPERF_SLURM_TEST_SIF"],
            "input_volumes": [
                {"host_path": str(data), "mount_path": "/mnt/data", "type": "directory"}
            ],
            "output_volumes": [
                {"host_path": str(out), "mount_path": "/mnt/out", "type": "directory"}
            ],
            "environment": {"MSG": "hello from the job"},
            "network": "none",
            "entrypoint": "sh",
            "command": [
                "-c",
                'cat /mnt/data/input.txt > /mnt/out/result.txt; echo "$MSG" >> '
                "/mnt/out/result.txt; echo container-ran",
            ],
        },
        container_runtime(),
        env_out=env,
    )
    # only the job script may provide the container environment
    monkeypatch.delenv("SINGULARITYENV_MSG", raising=False)

    image = os.environ["MEDPERF_SLURM_TEST_SIF"]

    # Act
    log = run_in_slurm(
        command,
        task="infer",
        env=env,
        paths_to_check=[image],
        image=image,
        image_arch=get_sif_architecture(image, container_runtime()),
    )

    # Assert
    assert "container-ran" in log
    assert (out / "result.txt").read_text() == "input-data\nhello from the job\n"
    # the architecture was read from the image and checked on the "node"
    [job_dir] = job_dirs()
    assert "node_arch=$(uname -m)" in open(os.path.join(job_dir, "job.sh")).read()


def python_in_container_command(code):
    return craft_singularity_run_command(
        {
            "remove_container": True,
            "user": f"{os.getuid()}:{os.getgid()}",
            "image": os.environ["MEDPERF_SLURM_TEST_SIF"],
            "network": "none",
            "entrypoint": "python3",
            "command": ["-c", code],
        },
        container_runtime(),
    )


def first_line_seen_while_running(command, timeout=60):
    results = {}

    def run():
        try:
            results["log"] = run_in_slurm(command, task="infer")
        except ExecutionError as e:
            results["error"] = e

    thread = threading.Thread(target=run)
    thread.start()
    seen_while_running = False
    deadline = time.time() + timeout
    while thread.is_alive() and time.time() < deadline:
        for job_dir in job_dirs():
            log_path = os.path.join(job_dir, "job.log")
            finished = os.path.exists(os.path.join(job_dir, "exit_code"))
            if not finished and os.path.exists(log_path):
                text = open(log_path).read()
                # Buffered output arrives in one burst at exit, with "late-line";
                # only "early-line" alone proves it was streamed while running.
                if "early-line" in text and "late-line" not in text:
                    seen_while_running = True
        time.sleep(0.2)
    thread.join(timeout=30)
    assert "error" not in results, results.get("error")
    assert "late-line" in results["log"]
    return seen_while_running


@pytest.mark.skipif(
    not os.environ.get("MEDPERF_SLURM_TEST_SIF") or container_runtime() is None,
    reason="set MEDPERF_SLURM_TEST_SIF (an image with python3) and install apptainer",
)
def test_container_output_streams_while_the_job_runs(monkeypatch):
    # The container prints a line with print() (stdout), then keeps working.
    code = "import time; print('early-line'); time.sleep(4); print('late-line')"
    command = python_in_container_command(code)

    # Control: without the unbuffered default, Python holds the line until exit.
    default_env = launcher.DEFAULT_CONTAINER_ENV
    monkeypatch.setattr(launcher, "DEFAULT_CONTAINER_ENV", {})
    assert not first_line_seen_while_running(command)

    # With MedPerf's default, the line reaches job.log while the job runs.
    monkeypatch.setattr(launcher, "DEFAULT_CONTAINER_ENV", default_env)
    for name in os.listdir(config.slurm_jobs_dir):
        shutil.rmtree(os.path.join(config.slurm_jobs_dir, name))
    assert first_line_seen_while_running(command)
