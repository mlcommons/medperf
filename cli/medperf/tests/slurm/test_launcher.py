import json
import os

import pytest

from medperf import config
from medperf.exceptions import ExecutionError, InvalidArgumentError
from medperf.slurm import launcher
from medperf.slurm.commands import JobRef, JobStatus
from medperf.slurm.job_script import (
    EXIT_ARCH_MISMATCH,
    EXIT_PATH_NOT_VISIBLE,
    EXIT_RUNTIME_NOT_FOUND,
)
from medperf.slurm.launcher import SlurmJob, evaluate_outcome
from medperf.ui.cli import CLI

PATCH_LAUNCHER = "medperf.slurm.launcher.{}"
COMMAND = ["apptainer", "run", "-eC", "/shared/img.sif"]


class FakeClock:
    # Advances by `step` seconds every time it is read

    def __init__(self, step=10):
        self.now = 0
        self.step = step

    def __call__(self):
        self.now += self.step
        return self.now


class NoWait:
    def wait(self, timeout=None):
        return False

    def set(self):
        pass

    def clear(self):
        pass


@pytest.fixture
def ui(mocker, package_init):
    # The launcher streams logs with print_subprocess_logs, which CLI and WebUI
    # implement but the abstract UI interface does not declare.
    ui = mocker.create_autospec(spec=CLI)
    config.ui = ui
    return ui


@pytest.fixture
def slurm_config(fs):
    config.launcher = "slurm"
    config.slurm_jobs_dir = "/shared/slurm_jobs"
    config.slurm_poll_interval = 1
    config.slurm_accounting_grace = 30
    fs.create_dir("/shared/slurm_jobs")


@pytest.fixture
def job(slurm_config):
    os.makedirs("/shared/slurm_jobs/j1")
    job = SlurmJob("/shared/slurm_jobs/j1", "infer")
    job.job = JobRef("100")
    job._wake = NoWait()
    return job


@pytest.fixture
def clock(mocker):
    clock = FakeClock()
    mocker.patch(PATCH_LAUNCHER.format("time.monotonic"), side_effect=clock)
    return clock


def statuses(mocker, *items):
    return mocker.patch(PATCH_LAUNCHER.format("commands.query_status"), side_effect=list(items))


def write_exit_code(job, rc):
    with open(job.exit_code_path, "w") as f:
        f.write(f"{rc}\n")


# ---------------------------------------------------------------- outcome


def test_success_requires_completed_state_and_zero_exit_code():
    assert evaluate_outcome(JobStatus("COMPLETED"), 0) is None


def test_completed_job_with_nonzero_container_exit_code_fails():
    assert "exited with code 3" in evaluate_outcome(JobStatus("COMPLETED"), 3)


def test_completed_job_without_exit_code_record_fails():
    reason = evaluate_outcome(JobStatus("COMPLETED"), None)
    assert "exit code was not recorded" in reason


def test_exit_code_file_alone_decides_when_scheduler_forgot_the_job():
    assert evaluate_outcome(JobStatus(None), 0) is None
    assert "code 1" in evaluate_outcome(JobStatus(None), 1)


@pytest.mark.parametrize(
    "state,exit_code,expected",
    [
        ("FAILED", 2, "exited with code 2"),
        ("FAILED", None, "failed before the container finished"),
        ("FAILED", 137, "killed by signal 9"),
        ("FAILED", EXIT_PATH_NOT_VISIBLE, "not visible on the compute node"),
        ("FAILED", EXIT_RUNTIME_NOT_FOUND, "container runtime"),
        ("FAILED", EXIT_ARCH_MISMATCH, "different CPU architecture"),
        ("TIMEOUT", None, "time limit"),
        ("OUT_OF_MEMORY", None, "out of memory"),
        ("CANCELLED", None, "outside MedPerf"),
        ("PREEMPTED", None, "preempted"),
        ("NODE_FAIL", None, "node failure"),
        ("BOOT_FAIL", None, "node failure"),
        ("DEADLINE", None, "deadline"),
        ("SPECIAL_EXIT", None, "SPECIAL_EXIT"),
    ],
)
def test_failure_reasons(state, exit_code, expected):
    assert expected in evaluate_outcome(JobStatus(state), exit_code)


def test_timeout_wins_over_exit_code_written_by_killed_container():
    # Slurm sends SIGTERM at the time limit; the script may still record 143.
    assert "time limit" in evaluate_outcome(JobStatus("TIMEOUT"), 143)


def test_cancelled_by_medperf_is_reported_as_such():
    reason = evaluate_outcome(JobStatus("CANCELLED"), None, cancelled_by_medperf=True)
    assert reason == "was cancelled by MedPerf"


def test_failed_without_exit_file_includes_accounting_exit_code():
    reason = evaluate_outcome(JobStatus("FAILED", exit_code=1, signal=0), None)
    assert "job exit code 1" in reason


# ---------------------------------------------------------------- monitoring


def test_wait_follows_pending_running_completed(mocker, job, clock):
    # Arrange
    query = statuses(
        mocker,
        JobStatus("PENDING", reason="Priority"),
        JobStatus("PENDING", reason="Resources"),
        JobStatus("RUNNING", node="n1"),
        JobStatus("COMPLETED", exit_code=0),
    )

    # Act
    status = job.wait()

    # Assert
    assert status.state == "COMPLETED"
    assert query.call_count == 4
    assert job.started_at is not None


def test_wait_tolerates_accounting_delay_then_uses_exit_code_file(mocker, job, clock):
    # The job left squeue but sacct has no record yet; the exit code file appears.
    def query(_):
        if query.calls == 2:
            write_exit_code(job, 0)
        query.calls += 1
        return JobStatus(None) if query.calls > 1 else JobStatus("RUNNING")

    query.calls = 0
    mocker.patch(PATCH_LAUNCHER.format("commands.query_status"), side_effect=query)

    # Act
    status = job.wait()

    # Assert
    assert status.state is None
    assert status.source == "exit_code_file"


def test_wait_gives_up_on_job_missing_longer_than_grace(mocker, job, clock):
    # Arrange
    mocker.patch(
        PATCH_LAUNCHER.format("commands.query_status"),
        side_effect=[JobStatus("RUNNING")] + [JobStatus(None)] * 20,
    )

    # Act & Assert
    with pytest.raises(ExecutionError, match="no longer reported"):
        job.wait()


def test_wait_reports_unknown_job(mocker, job, clock):
    mocker.patch(
        PATCH_LAUNCHER.format("commands.query_status"),
        return_value=JobStatus(None, error="Socket timed out"),
    )
    with pytest.raises(ExecutionError, match="unknown to squeue and sacct.*Socket"):
        job.wait()


def test_wait_recovers_when_job_reappears_within_grace(mocker, job, clock):
    # transient controller errors must not fail the task
    statuses(
        mocker,
        JobStatus("RUNNING"),
        JobStatus(None, error="timeout"),
        JobStatus("RUNNING"),
        JobStatus(None, error="timeout"),
        JobStatus("COMPLETED"),
    )
    assert job.wait().state == "COMPLETED"


def test_medperf_timeout_counts_running_time_only(mocker, job, clock):
    # Arrange: pending for many polls, then running beyond the timeout
    query = statuses(
        mocker,
        *[JobStatus("PENDING")] * 10,
        *[JobStatus("RUNNING")] * 10,
    )

    # Act & Assert
    with pytest.raises(ExecutionError, match="MedPerf timeout of 25 seconds"):
        job.wait(timeout=25)
    # the clock only starts once the job runs: all 10 pending polls passed
    assert query.call_count > 10


def test_wait_streams_new_log_lines(mocker, job, clock, ui):
    # Arrange
    def query(_):
        query.calls += 1
        with open(job.log_path, "a") as f:
            f.write(f"line {query.calls}\n")
        return JobStatus("COMPLETED" if query.calls == 3 else "RUNNING")

    query.calls = 0
    mocker.patch(PATCH_LAUNCHER.format("commands.query_status"), side_effect=query)

    # Act
    job.wait()

    # Assert
    printed = [c.args[0] for c in ui.print_subprocess_logs.call_args_list]
    assert [p for p in printed if "line" in p] and len(printed) == 3


def test_partial_log_lines_are_held_until_complete(job, ui):
    # Arrange
    with open(job.log_path, "w") as f:
        f.write("complete\npart")

    # Act
    job.stream_new_log_output()
    with open(job.log_path, "a") as f:
        f.write("ial\n")
    job.stream_new_log_output()

    # Assert
    printed = [c.args[0] for c in ui.print_subprocess_logs.call_args_list]
    assert len(printed) == 2
    assert "complete" in printed[0]
    assert "partial" in printed[1]


def test_missing_log_file_is_not_an_error_while_pending(job, ui):
    job.stream_new_log_output()
    ui.print_subprocess_logs.assert_not_called()


# ---------------------------------------------------------------- cancellation


def test_killpg_cancels_the_slurm_job_once(mocker, job):
    # Arrange
    cancel = mocker.patch(PATCH_LAUNCHER.format("commands.cancel"), return_value=True)

    # Act
    job.killpg()
    job.killpg()

    # Assert
    cancel.assert_called_once()
    assert cancel.call_args[0][0].job_id == "100"
    assert job.cancel_requested


def test_cancel_failure_tells_user_how_to_cancel(mocker, job, ui):
    # Arrange
    mocker.patch(
        PATCH_LAUNCHER.format("commands.cancel"), side_effect=ExecutionError("scancel missing")
    )

    # Act
    job.cancel()

    # Assert
    assert "scancel 100" in ui.print_warning.call_args[0][0]


def test_cancel_before_submission_is_a_noop(mocker, slurm_config):
    cancel = mocker.patch(PATCH_LAUNCHER.format("commands.cancel"))
    SlurmJob("/shared/slurm_jobs", "infer").cancel()
    cancel.assert_not_called()


# ---------------------------------------------------------------- run_in_slurm


@pytest.fixture
def submit(mocker, slurm_config):
    mocker.patch(PATCH_LAUNCHER.format("commands.check_slurm_available"))
    return mocker.patch(PATCH_LAUNCHER.format("commands.submit"), return_value=JobRef("200"))


def finish_job(rc, log="container output\n"):
    # query_status side effect that makes the job finish with exit code rc

    def query(job_ref):
        job_dir = query.job_dir()
        with open(os.path.join(job_dir, "job.log"), "w") as f:
            f.write(log)
        if rc is not None:
            with open(os.path.join(job_dir, "exit_code"), "w") as f:
                f.write(str(rc))
        return JobStatus("COMPLETED" if rc == 0 else "FAILED")

    query.job_dir = lambda: next(
        os.path.join("/shared/slurm_jobs", d) for d in os.listdir("/shared/slurm_jobs")
    )
    return query


def test_run_in_slurm_success_writes_output_logs(mocker, submit, ui):
    # Arrange
    mocker.patch(PATCH_LAUNCHER.format("commands.query_status"), side_effect=finish_job(0))

    # Act
    out = launcher.run_in_slurm(
        COMMAND, output_logs="/shared/model.log", task="infer"
    )

    # Assert
    assert out == "container output\n"
    with open("/shared/model.log") as f:
        assert f.read() == "container output\n"
    assert "infer" not in config.running_containers


def test_run_in_slurm_writes_script_with_configured_resources(mocker, submit, ui):
    # Arrange
    config.slurm_partition = "booster"
    config.slurm_account = "myproj"
    config.slurm_extra_args = "--qos=normal"
    mocker.patch(PATCH_LAUNCHER.format("commands.query_status"), side_effect=finish_job(0))

    # Act
    launcher.run_in_slurm(
        COMMAND, task="infer", env={"SINGULARITYENV_X": "1"}, paths_to_check=["/i"]
    )

    # Assert
    script_path, extra_args = submit.call_args[0]
    assert extra_args == ["--qos=normal"]
    with open(script_path) as f:
        script = f.read()
    assert "#SBATCH --partition=booster" in script
    assert "#SBATCH --account=myproj" in script
    assert "export SINGULARITYENV_X=1" in script
    assert oct(os.stat(script_path).st_mode & 0o777) == oct(0o600)


def test_run_in_slurm_records_status_file(mocker, submit, ui):
    # Arrange
    mocker.patch(PATCH_LAUNCHER.format("commands.query_status"), side_effect=finish_job(5))

    # Act
    with pytest.raises(ExecutionError, match="exited with code 5"):
        launcher.run_in_slurm(COMMAND, task="evaluate")

    # Assert
    job_dir = finish_job(0).job_dir()
    with open(os.path.join(job_dir, "medperf_status.json")) as f:
        record = json.load(f)
    assert record["job_id"] == "200"
    assert record["state"] == "FAILED"
    assert record["exit_code"] == 5


def test_run_in_slurm_explains_missing_log(mocker, submit, ui):
    mocker.patch(
        PATCH_LAUNCHER.format("commands.query_status"),
        return_value=JobStatus("FAILED", exit_code=1, signal=0),
    )
    with pytest.raises(ExecutionError, match="No job log was written"):
        launcher.run_in_slurm(COMMAND, task="infer")


def test_run_in_slurm_registers_job_for_webui_stop(mocker, submit, ui):
    # Arrange
    seen = {}

    def query(_):
        seen["job"] = config.running_containers.get("infer")
        return finish_job(0)(_)

    mocker.patch(PATCH_LAUNCHER.format("commands.query_status"), side_effect=query)

    # Act
    launcher.run_in_slurm(COMMAND, task="infer")

    # Assert
    assert isinstance(seen["job"], SlurmJob)
    assert "infer" not in config.running_containers


@pytest.mark.parametrize("exception", [KeyboardInterrupt, ExecutionError])
def test_run_in_slurm_cancels_job_when_monitoring_stops(mocker, submit, ui, exception):
    # Arrange
    mocker.patch(PATCH_LAUNCHER.format("commands.query_status"), side_effect=exception)
    cancel = mocker.patch(PATCH_LAUNCHER.format("commands.cancel"), return_value=True)

    # Act & Assert
    with pytest.raises(exception):
        launcher.run_in_slurm(COMMAND, task="infer")
    cancel.assert_called_once()
    assert cancel.call_args[0][0].job_id == "200"
    assert "infer" not in config.running_containers


def test_run_in_slurm_does_not_submit_invalid_resources(mocker, submit, ui):
    config.slurm_time = "two hours"
    with pytest.raises(Exception, match="Invalid Slurm time"):
        launcher.run_in_slurm(COMMAND, task="infer")
    submit.assert_not_called()


def test_run_in_slurm_warns_about_node_local_paths(mocker, submit, ui, fs):
    # Arrange
    mocker.patch(PATCH_LAUNCHER.format("commands.query_status"), side_effect=finish_job(0))

    # Act
    launcher.run_in_slurm(COMMAND, task="infer", paths_to_check=["/tmp/img.sif"])

    # Assert
    warnings = " ".join(c.args[0] for c in ui.print_warning.call_args_list)
    assert "/tmp/img.sif is on node-local storage" in warnings


def test_run_in_slurm_warns_when_gpus_are_not_requested(mocker, submit, ui):
    mocker.patch(PATCH_LAUNCHER.format("commands.query_status"), side_effect=finish_job(0))
    launcher.run_in_slurm(COMMAND, task="infer", gpu_enabled=True)
    warnings = " ".join(c.args[0] for c in ui.print_warning.call_args_list)
    assert "no GPUs were requested" in warnings


def test_run_in_slurm_warns_when_container_cannot_use_requested_gpus(
    mocker, submit, ui
):
    config.slurm_gres = "gpu:4"
    mocker.patch(PATCH_LAUNCHER.format("commands.query_status"), side_effect=finish_job(0))
    launcher.run_in_slurm(COMMAND, task="infer", gpu_enabled=False)
    warnings = " ".join(c.args[0] for c in ui.print_warning.call_args_list)
    assert "--gpus=all" in warnings


def test_default_jobs_dir_is_under_logs_storage(slurm_config):
    config.slurm_jobs_dir = None
    expected = os.path.join(str(config.logs_storage), "slurm_jobs")
    assert launcher.get_jobs_dir() == os.path.abspath(expected)


@pytest.mark.parametrize(
    "path,expected",
    [("/tmp/x", True), ("/dev/shm", True), ("/tmpfoo/x", False), ("/p/x", False)],
)
def test_is_node_local(path, expected):
    assert launcher.is_node_local(path) is expected


# ---------------------------------------------------------------- architecture


@pytest.fixture
def login_node_arch(mocker):
    def set_arch(arch):
        mocker.patch(PATCH_LAUNCHER.format("platform.machine"), return_value=arch)

    return set_arch


def test_architecture_check_rejects_image_for_other_cpu(login_node_arch):
    # Arrange: an amd64 image on an Arm (JUPITER-like) login node
    login_node_arch("aarch64")

    # Act & Assert
    with pytest.raises(InvalidArgumentError, match="built for amd64.*nodes are arm64"):
        launcher.check_image_architecture("/i/model.sif", "amd64")


def test_architecture_check_accepts_matching_image(login_node_arch):
    login_node_arch("aarch64")
    launcher.check_image_architecture("/i/model.sif", "arm64")


def test_architecture_check_uses_configured_node_arch(login_node_arch):
    # x86 login node, Arm compute nodes
    login_node_arch("x86_64")
    config.slurm_node_arch = "aarch64"
    launcher.check_image_architecture("/i/model.sif", "arm64")
    with pytest.raises(InvalidArgumentError, match="from --slurm-node-arch"):
        launcher.check_image_architecture("/i/model.sif", "amd64")


def test_architecture_check_skipped_when_image_arch_unknown(login_node_arch):
    login_node_arch("aarch64")
    launcher.check_image_architecture("/i/model.sif", None)


def test_run_in_slurm_does_not_submit_image_for_other_cpu(
    mocker, submit, ui, login_node_arch
):
    # Arrange
    login_node_arch("aarch64")

    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        launcher.run_in_slurm(
            COMMAND, task="infer", image="/i/model.sif", image_arch="amd64"
        )
    submit.assert_not_called()


def test_run_in_slurm_passes_image_arch_to_the_job_check(
    mocker, submit, ui, login_node_arch
):
    # Arrange
    login_node_arch("x86_64")
    mocker.patch(PATCH_LAUNCHER.format("commands.query_status"), side_effect=finish_job(0))

    # Act
    launcher.run_in_slurm(COMMAND, task="infer", image="/i/m.sif", image_arch="amd64")

    # Assert
    with open(submit.call_args[0][0]) as f:
        assert 'if [ "$node_arch" != amd64 ]; then' in f.read()


def test_exec_format_error_in_log_is_explained(mocker, submit, ui):
    mocker.patch(
        PATCH_LAUNCHER.format("commands.query_status"),
        side_effect=finish_job(255, log="FATAL: ... exec format error\n"),
    )
    with pytest.raises(ExecutionError, match="different CPU architecture"):
        launcher.run_in_slurm(COMMAND, task="infer")


# ---------------------------------------------------------------- output buffering


def script_of(submit):
    with open(submit.call_args[0][0]) as f:
        return f.read()


def test_containers_get_unbuffered_python_output_by_default(mocker, submit, ui):
    mocker.patch(PATCH_LAUNCHER.format("commands.query_status"), side_effect=finish_job(0))
    launcher.run_in_slurm(COMMAND, task="infer")
    assert "export SINGULARITYENV_PYTHONUNBUFFERED=1" in script_of(submit)


def test_container_config_can_override_unbuffered_default(mocker, submit, ui):
    mocker.patch(PATCH_LAUNCHER.format("commands.query_status"), side_effect=finish_job(0))
    launcher.run_in_slurm(
        COMMAND, task="infer", env={"SINGULARITYENV_PYTHONUNBUFFERED": "0"}
    )
    script = script_of(submit)
    assert "export SINGULARITYENV_PYTHONUNBUFFERED=0" in script
    assert "SINGULARITYENV_PYTHONUNBUFFERED=1" not in script


# ---------------------------------------------------------------- live log streaming


def test_log_lines_are_printed_between_status_checks(mocker, job, ui):
    # Arrange: a clock advancing 1 s per read, and a wait that returns at once
    clock = FakeClock(step=1)
    mocker.patch(PATCH_LAUNCHER.format("time.monotonic"), side_effect=clock)
    with open(job.log_path, "w") as f:
        f.write("epoch 1\n")

    # Act: wait for a 5 s poll interval
    job._sleep_streaming_logs(5)

    # Assert: the log was read during the wait, not only at the next status check
    printed = [c.args[0] for c in ui.print_subprocess_logs.call_args_list]
    assert any("epoch 1" in p for p in printed)


def test_cancel_ends_the_wait_immediately(mocker, slurm_config, ui):
    # Arrange: a real event, already set by cancel()
    os.makedirs("/shared/slurm_jobs/j2")
    job = SlurmJob("/shared/slurm_jobs/j2", "infer")
    job._wake.set()
    stream = mocker.patch.object(job, "stream_new_log_output")

    # Act
    job._sleep_streaming_logs(30)

    # Assert: returned without waiting out the poll interval
    stream.assert_not_called()
    assert not job._wake.is_set()
