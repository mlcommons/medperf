"""The top-level `medperf run` command."""

import pytest

from medperf.cli import execute
from medperf.tests.mocks.execution import TestExecution

PATCH_CLI = "medperf.cli.{}"


@pytest.fixture()
def run_command(mocker, ui, fs):
    """`medperf run`, with the execution itself stubbed out.

    The typer callback is called directly: building the whole command group
    needs every other subcommand's signature, and one of them uses a type typer
    cannot render."""
    mocker.patch(
        PATCH_CLI.format("DatasetBenchmarkRun.run"),
        return_value=[TestExecution(id=9)],
    )
    return mocker.patch("medperf.commands.execution.submit.ResultSubmission.run")


def test_running_does_not_report_the_results(run_command, ui):
    """Reporting a number to a benchmark is a decision of its own, not a side
    effect of computing it"""
    # Act
    execute(
        benchmark_uid=1,
        data_uid=2,
        model_uid=3,
        ignore_model_errors=False,
        no_cache=False,
        new_result=False,
    )

    # Assert
    run_command.assert_not_called()
    printed = "\n".join(str(call) for call in ui.print.call_args_list)
    assert "medperf result submit -r 9" in printed
