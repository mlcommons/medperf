import os
from copy import deepcopy

import pytest
import semver

from medperf import config
from medperf.containers.parsers.simple_container import SimpleContainerParser
from medperf.containers.runners import load_runner
from medperf.containers.runners.docker_runner import DockerRunner
from medperf.containers.runners.singularity_runner import SingularityRunner
from medperf.containers.runners import singularity_utils
from medperf.containers.runners.singularity_utils import craft_singularity_run_command
from medperf.exceptions import InvalidArgumentError

PATCH_RUNNER = "medperf.containers.runners.singularity_runner.{}"

CONTAINER_CONFIG = {
    "container_type": "SingularityFile",
    "image": "https://example.com/model.sif",
    "tasks": {
        "infer": {
            "run_args": {"environment": {"MODEL_FLAG": "on"}},
            "input_volumes": {
                "data_path": {"mount_path": "/mlcommons/volumes/data", "type": "directory"}
            },
            "output_volumes": {
                "output_path": {"mount_path": "/mlcommons/volumes/out", "type": "directory"}
            },
        }
    },
}


def parser():
    # SingularityRunner.run mutates the run_args of the config it is given, so
    # every runner gets its own copy.
    return SimpleContainerParser(deepcopy(CONTAINER_CONFIG), ["docker", "singularity"])


def make_runner():
    runner = SingularityRunner(parser())
    runner.image_file_path = "/shared/images/model.sif"
    return runner


@pytest.fixture
def runner(mocker, fs):
    mocker.patch(
        PATCH_RUNNER.format("get_singularity_executable_props"),
        return_value=("apptainer", "apptainer", semver.VersionInfo(1, 3, 4)),
    )
    fs.create_dir("/shared/data")
    fs.create_file("/shared/images/model.sif")
    return make_runner()


def run(runner, **kwargs):
    defaults = dict(
        task="infer",
        tmp_folder="/shared/tmp/abc",
        output_logs="/shared/logs/model.log",
        timeout=600,
        medperf_mounts={"data_path": "/shared/data", "output_path": "/shared/out"},
    )
    defaults.update(kwargs)
    runner.run(**defaults)


def test_load_runner_rejects_docker_with_slurm(mocker):
    config.launcher = "slurm"
    config.platform = "docker"
    with pytest.raises(InvalidArgumentError, match="--platform singularity"):
        load_runner(parser())


def test_load_runner_rejects_unknown_launcher():
    config.launcher = "pbs"
    with pytest.raises(InvalidArgumentError, match="Invalid launcher"):
        load_runner(parser())


def test_load_runner_keeps_docker_for_local_launcher():
    config.launcher = "local"
    config.platform = "docker"
    assert isinstance(load_runner(parser()), DockerRunner)


def test_local_launcher_still_runs_container_locally(mocker, runner):
    # Arrange
    config.launcher = "local"
    local = mocker.patch(PATCH_RUNNER.format("run_command"))
    slurm = mocker.patch(PATCH_RUNNER.format("run_in_slurm"))

    # Act
    run(runner)

    # Assert
    local.assert_called_once()
    slurm.assert_not_called()


def test_slurm_launcher_submits_the_same_container_command(mocker, runner):
    # Arrange
    config.launcher = "local"
    local = mocker.patch(PATCH_RUNNER.format("run_command"))
    run(runner)
    local_command = local.call_args[0][0]

    config.launcher = "slurm"
    slurm = mocker.patch(PATCH_RUNNER.format("run_in_slurm"))
    mocker.patch(PATCH_RUNNER.format("get_sif_architecture"), return_value="arm64")

    # Act
    run(make_runner())

    # Assert
    args, kwargs = slurm.call_args
    assert args[0] == local_command
    assert kwargs["task"] == "infer"
    assert kwargs["timeout"] == 600
    assert kwargs["output_logs"] == "/shared/logs/model.log"
    assert kwargs["paths_to_check"] == ["/shared/images/model.sif"]
    assert kwargs["gpu_enabled"] is False
    assert kwargs["image"] == "/shared/images/model.sif"
    assert kwargs["image_arch"] == "arm64"


def test_slurm_launcher_passes_container_environment_explicitly(mocker, runner):
    # Arrange
    config.launcher = "slurm"
    config.container_loglevel = None
    slurm = mocker.patch(PATCH_RUNNER.format("run_in_slurm"))

    # Act
    run(runner, medperf_env={"MEDPERF_LOGLEVEL": "DEBUG"})

    # Assert
    env = slurm.call_args[1]["env"]
    assert env == {
        "SINGULARITYENV_MODEL_FLAG": "on",
        "SINGULARITYENV_MEDPERF_LOGLEVEL": "DEBUG",
    }


def test_slurm_launcher_enables_gpus_for_gpus_all(mocker, runner):
    config.launcher = "slurm"
    config.gpus = "all"
    slurm = mocker.patch(PATCH_RUNNER.format("run_in_slurm"))
    run(runner)
    assert "--nv" in slurm.call_args[0][0]
    assert slurm.call_args[1]["gpu_enabled"] is True


def test_slurm_launcher_rejects_specific_gpu_ids(mocker, runner):
    config.launcher = "slurm"
    config.gpus = "device=0,1"
    mocker.patch(PATCH_RUNNER.format("run_in_slurm"))
    with pytest.raises(InvalidArgumentError, match="assigned by Slurm"):
        run(runner)


def test_slurm_launcher_rejects_tasks_publishing_ports(mocker, runner):
    config.launcher = "slurm"
    slurm = mocker.patch(PATCH_RUNNER.format("run_in_slurm"))
    with pytest.raises(InvalidArgumentError, match="ports"):
        run(runner, ports=["0.0.0.0:80:80"], disable_network=False)
    slurm.assert_not_called()


def test_slurm_launcher_warns_for_network_tasks(mocker, runner, ui):
    config.launcher = "slurm"
    mocker.patch(PATCH_RUNNER.format("run_in_slurm"))
    run(runner, disable_network=False)
    assert "network access" in ui.print_warning.call_args[0][0]


def test_craft_command_collects_environment(mocker):
    # Arrange
    mocker.patch.dict(os.environ, {}, clear=False)
    run_args = {
        "remove_container": True,
        "user": "1:1",
        "image": "/img.sif",
        "environment": {"A": "1"},
        "network": "none",
    }
    env = {}

    # Act
    command = craft_singularity_run_command(run_args, "apptainer", env_out=env)

    # Assert
    assert env == {"SINGULARITYENV_A": "1"}
    assert os.environ["SINGULARITYENV_A"] == "1"  # existing behavior preserved
    assert command[:3] == ["apptainer", "run", "-eC"]


def test_prepare_report_watcher_polls_under_slurm(mocker):
    # Arrange
    from medperf.commands.dataset import prepare

    polling = mocker.patch.object(prepare, "PollingObserver")
    inotify = mocker.patch.object(prepare, "Observer")
    # prepare.config may be a different module object than this file's `config`
    # after the conftest reloads it, so patch the one prepare actually reads.
    mocker.patch.object(prepare.config, "launcher", "slurm")
    preparation = mocker.Mock()
    preparation.dataset.path = "/shared/dataset"

    # Act
    prepare.ReportSender(preparation).start()
    prepare.config.launcher = "local"
    prepare.ReportSender(preparation).start()

    # Assert
    polling.assert_called_once()
    inotify.assert_called_once()


SIF_LIST_OUTPUT = """------------------------------------------------------------------------------
ID   |GROUP   |LINK    |SIF POSITION (start-end)  |TYPE
------------------------------------------------------------------------------
1    |1       |NONE    |32176-32233               |Def.FILE
2    |1       |NONE    |32233-35761               |JSON.Generic
4    |1       |NONE    |36864-47673344            |FS (Squashfs/*System/{arch})
"""


@pytest.mark.parametrize("arch", ["amd64", "arm64"])
def test_get_sif_architecture_reads_image_metadata(mocker, arch):
    # Arrange
    run = mocker.patch.object(
        singularity_utils.subprocess,
        "run",
        return_value=mocker.Mock(returncode=0, stdout=SIF_LIST_OUTPUT.format(arch=arch)),
    )

    # Act
    result = singularity_utils.get_sif_architecture("/i/m.sif", "apptainer")

    # Assert
    assert result == arch
    assert run.call_args[0][0] == ["apptainer", "sif", "list", "/i/m.sif"]


@pytest.mark.parametrize(
    "outcome",
    [
        {"side_effect": FileNotFoundError},
        {"return_value": "failed"},
        {"return_value": "unparsable"},
    ],
)
def test_get_sif_architecture_returns_none_when_unknown(mocker, outcome):
    if outcome.get("return_value") == "failed":
        outcome = {"return_value": mocker.Mock(returncode=255, stdout="", stderr="x")}
    elif outcome.get("return_value") == "unparsable":
        outcome = {"return_value": mocker.Mock(returncode=0, stdout="no fs here")}
    mocker.patch.object(singularity_utils.subprocess, "run", **outcome)
    assert singularity_utils.get_sif_architecture("/i/m.sif", "apptainer") is None
