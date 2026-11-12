import os
import subprocess

import pytest

from medperf.exceptions import SlurmCommandError, SlurmCommandNotFound
from medperf.slurm import commands
from medperf.slurm.commands import JobRef, JobStatus

PATCH_COMMANDS = "medperf.slurm.commands.{}"


def completed(args=None, returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(args or [], returncode, stdout, stderr)


@pytest.mark.parametrize(
    "stdout,job_id,cluster",
    [
        ("12345\n", "12345", None),
        ("12345;jupiter\n", "12345", "jupiter"),
        ("Submission note from site plugin\n777\n", "777", None),
        ("  42  ", "42", None),
    ],
)
def test_parse_sbatch_output(stdout, job_id, cluster):
    # Act
    job = commands.parse_sbatch_output(stdout)

    # Assert
    assert job.job_id == job_id
    assert job.cluster == cluster


@pytest.mark.parametrize("stdout", ["", "Submitted batch job 12", "abc;def"])
def test_parse_sbatch_output_rejects_unparsable_output(stdout):
    with pytest.raises(SlurmCommandError):
        commands.parse_sbatch_output(stdout)


def test_job_ref_adds_clusters_option_only_when_cluster_is_known():
    assert JobRef("1").cluster_args() == []
    assert JobRef("1", "c1").cluster_args() == ["--clusters=c1"]


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("RUNNING", "RUNNING"),
        ("CANCELLED by 1234", "CANCELLED"),
        ("cd", "COMPLETED"),
        ("PD", "PENDING"),
        ("OOM", "OUT_OF_MEMORY"),
        ("TO", "TIMEOUT"),
        ("COMPLETED+", "COMPLETED"),
        ("", None),
        ("   ", None),
    ],
)
def test_normalize_state(raw, expected):
    assert commands.normalize_state(raw) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [("0:0", (0, 0)), ("1:0", (1, 0)), ("0:9", (0, 9)), ("", (None, None))],
)
def test_parse_exit_code(raw, expected):
    assert commands.parse_exit_code(raw) == expected


def test_parse_squeue_output_pending_with_reason():
    # Act
    status = commands.parse_squeue_output("PENDING|Priority|\n")

    # Assert
    assert status.state == "PENDING"
    assert status.reason == "Priority"
    assert status.node is None
    assert not status.is_terminal


def test_parse_squeue_output_running_on_node():
    # Act
    status = commands.parse_squeue_output("RUNNING|None|jpbo-012-01\n")

    # Assert
    assert status.state == "RUNNING"
    assert status.reason is None
    assert status.node == "jpbo-012-01"


def test_parse_squeue_output_empty_means_unknown():
    assert not commands.parse_squeue_output("\n").is_known


def test_parse_sacct_output_ignores_other_job_ids_and_keeps_last_record():
    # Arrange
    stdout = "99|COMPLETED|0:0|n1\n12|FAILED|1:0|n2\n12|CANCELLED by 1000|0:15|n3\n"

    # Act
    status = commands.parse_sacct_output(stdout, "12")

    # Assert
    assert status.state == "CANCELLED"
    assert status.exit_code == 0
    assert status.signal == 15
    assert status.node == "n3"
    assert status.is_terminal


def test_parse_sacct_output_pending_job_has_no_node():
    status = commands.parse_sacct_output("12|PENDING|0:0|None assigned\n", "12")
    assert status.state == "PENDING"
    assert status.node is None


def test_parse_sacct_output_without_record_is_unknown():
    assert not commands.parse_sacct_output("", "12").is_known


def test_run_raises_not_found_for_missing_executable(mocker):
    # Arrange
    mocker.patch(PATCH_COMMANDS.format("subprocess.run"), side_effect=FileNotFoundError)

    # Act & Assert
    with pytest.raises(SlurmCommandNotFound):
        commands._run(["squeue"])


def test_run_raises_on_unresponsive_command(mocker):
    # Arrange
    mocker.patch(
        PATCH_COMMANDS.format("subprocess.run"),
        side_effect=subprocess.TimeoutExpired("squeue", 1),
    )

    # Act & Assert
    with pytest.raises(SlurmCommandError):
        commands._run(["squeue"], timeout=1)


def test_run_uses_argument_list_without_shell(mocker):
    # Arrange
    spy = mocker.patch(
        PATCH_COMMANDS.format("subprocess.run"), return_value=completed()
    )

    # Act
    commands._run(["scancel", "1; rm -rf /"])

    # Assert
    args, kwargs = spy.call_args
    assert args[0] == ["scancel", "1; rm -rf /"]
    assert not kwargs.get("shell", False)


def test_check_slurm_available_raises_without_sbatch(mocker):
    mocker.patch(PATCH_COMMANDS.format("shutil.which"), return_value=None)
    with pytest.raises(SlurmCommandNotFound):
        commands.check_slurm_available()


def test_submit_returns_job_ref(mocker):
    # Arrange
    spy = mocker.patch(
        PATCH_COMMANDS.format("_run"), return_value=completed(stdout="314;c1\n")
    )

    # Act
    job = commands.submit("/jobs/job.sh", ["--qos=normal"])

    # Assert
    assert job.job_id == "314"
    assert job.cluster == "c1"
    spy.assert_called_once()
    assert spy.call_args[0][0] == [
        "sbatch",
        "--parsable",
        "--qos=normal",
        "/jobs/job.sh",
    ]


def test_submit_does_not_pass_leftover_container_env_to_sbatch(mocker, monkeypatch):
    # Arrange: medperf's own environment after an earlier task
    monkeypatch.setenv("SINGULARITYENV_LEFTOVER", "stale")
    monkeypatch.setenv("APPTAINERENV_LEFTOVER", "stale")
    monkeypatch.setenv("APPTAINER_CACHEDIR", "/p/cache")
    run = mocker.patch(
        PATCH_COMMANDS.format("subprocess.run"), return_value=completed(stdout="1\n")
    )

    # Act
    commands.submit("/jobs/job.sh")

    # Assert
    env = run.call_args[1]["env"]
    assert "SINGULARITYENV_LEFTOVER" not in env
    assert "APPTAINERENV_LEFTOVER" not in env
    assert env["APPTAINER_CACHEDIR"] == "/p/cache"
    assert env["PATH"] == os.environ["PATH"]


def test_other_slurm_commands_keep_the_inherited_environment(mocker):
    run = mocker.patch(PATCH_COMMANDS.format("subprocess.run"), return_value=completed())
    commands.cancel(JobRef("1"))
    assert run.call_args[1]["env"] is None


def test_submit_rejection_reports_sbatch_message(mocker):
    # Arrange
    message = (
        "sbatch: error: Batch job submission failed: "
        "Invalid account or account/partition combination specified"
    )
    mocker.patch(
        PATCH_COMMANDS.format("_run"),
        return_value=completed(returncode=1, stderr=message),
    )

    # Act & Assert
    with pytest.raises(SlurmCommandError, match="Invalid account"):
        commands.submit("/jobs/job.sh")


def test_query_squeue_treats_invalid_job_id_as_unknown_not_error(mocker):
    # Arrange
    mocker.patch(
        PATCH_COMMANDS.format("_run"),
        return_value=completed(
            returncode=1,
            stderr="slurm_load_jobs error: Invalid job id specified",
        ),
    )

    # Act
    status = commands.query_squeue(JobRef("1"))

    # Assert
    assert not status.is_known
    assert status.error is None


def test_query_squeue_reports_controller_errors(mocker):
    # Arrange
    mocker.patch(
        PATCH_COMMANDS.format("_run"),
        return_value=completed(returncode=1, stderr="Socket timed out"),
    )

    # Act
    status = commands.query_squeue(JobRef("1"))

    # Assert
    assert not status.is_known
    assert "Socket timed out" in status.error


def test_query_squeue_passes_cluster_and_job(mocker):
    # Arrange
    spy = mocker.patch(
        PATCH_COMMANDS.format("_run"), return_value=completed(stdout="RUNNING|None|n\n")
    )

    # Act
    commands.query_squeue(JobRef("5", "c1"))

    # Assert
    args = spy.call_args[0][0]
    assert args[0] == "squeue"
    assert "--clusters=c1" in args
    assert "--jobs=5" in args
    assert "--states=all" in args


def test_query_sacct_reports_disabled_accounting(mocker):
    # Arrange
    mocker.patch(PATCH_COMMANDS.format("shutil.which"), return_value="/usr/bin/sacct")
    mocker.patch(
        PATCH_COMMANDS.format("_run"),
        return_value=completed(
            returncode=1, stderr="Slurm accounting storage is disabled"
        ),
    )

    # Act
    status = commands.query_sacct(JobRef("1"))

    # Assert
    assert not status.is_known
    assert "disabled" in status.error


def test_query_sacct_without_sacct_installed(mocker):
    mocker.patch(PATCH_COMMANDS.format("shutil.which"), return_value=None)
    status = commands.query_sacct(JobRef("1"))
    assert not status.is_known
    assert status.error == "sacct not available"


def test_query_status_prefers_active_squeue_state(mocker):
    # Arrange
    mocker.patch(
        PATCH_COMMANDS.format("query_squeue"),
        return_value=JobStatus("RUNNING", source="squeue"),
    )
    sacct = mocker.patch(PATCH_COMMANDS.format("query_sacct"))

    # Act
    status = commands.query_status(JobRef("1"))

    # Assert
    assert status.state == "RUNNING"
    sacct.assert_not_called()


def test_query_status_uses_accounting_for_finished_jobs(mocker):
    # Arrange
    mocker.patch(
        PATCH_COMMANDS.format("query_squeue"),
        return_value=JobStatus("COMPLETED", source="squeue"),
    )
    mocker.patch(
        PATCH_COMMANDS.format("query_sacct"),
        return_value=JobStatus("COMPLETED", exit_code=0, signal=0, source="sacct"),
    )

    # Act
    status = commands.query_status(JobRef("1"))

    # Assert
    assert status.source == "sacct"
    assert status.exit_code == 0


def test_query_status_ignores_lagging_accounting(mocker):
    # squeue already says the job failed; accounting still says RUNNING
    mocker.patch(
        PATCH_COMMANDS.format("query_squeue"),
        return_value=JobStatus("FAILED", source="squeue"),
    )
    mocker.patch(
        PATCH_COMMANDS.format("query_sacct"),
        return_value=JobStatus("RUNNING", source="sacct"),
    )

    # Act
    status = commands.query_status(JobRef("1"))

    # Assert
    assert status.state == "FAILED"
    assert status.source == "squeue"


def test_query_status_falls_back_to_squeue_terminal_state_without_accounting(mocker):
    mocker.patch(
        PATCH_COMMANDS.format("query_squeue"),
        return_value=JobStatus("TIMEOUT", source="squeue"),
    )
    mocker.patch(
        PATCH_COMMANDS.format("query_sacct"),
        return_value=JobStatus(None, source="sacct", error="sacct not available"),
    )

    assert commands.query_status(JobRef("1")).state == "TIMEOUT"


def test_query_status_unknown_job_collects_errors(mocker):
    mocker.patch(
        PATCH_COMMANDS.format("query_squeue"),
        return_value=JobStatus(None, source="squeue", error="Socket timed out"),
    )
    mocker.patch(
        PATCH_COMMANDS.format("query_sacct"),
        return_value=JobStatus(None, source="sacct"),
    )

    # Act
    status = commands.query_status(JobRef("1"))

    # Assert
    assert not status.is_known
    assert "Socket timed out" in status.error


def test_cancel_targets_only_the_given_job(mocker):
    # Arrange
    spy = mocker.patch(PATCH_COMMANDS.format("_run"), return_value=completed())

    # Act
    result = commands.cancel(JobRef("77", "c1"))

    # Assert
    assert result
    spy.assert_called_once_with(["scancel", "--clusters=c1", "77"])


def test_cancel_of_finished_job_is_not_an_error(mocker):
    mocker.patch(
        PATCH_COMMANDS.format("_run"),
        return_value=completed(
            returncode=1,
            stderr="scancel: error: Kill job error on job id 77: Job/step already "
            "completing or completed",
        ),
    )
    assert commands.cancel(JobRef("77")) is False
