import pytest

from medperf.containers.parsers.simple_container import SimpleContainerParser
from medperf.exceptions import InvalidContainerSpec


def _preparator_config(
    include_statistics=True,
    include_statistics_output=True,
    command="python3 -m prep_workflow.main --start=sanity_check",
    extra_tasks=None,
):
    tasks = {
        "prepare": {
            "run_args": {"command": "python3 -m prep_workflow.main"},
            "input_volumes": {
                "data_path": {"mount_path": "/raw", "type": "directory"},
            },
            "output_volumes": {
                "output_path": {"mount_path": "/data", "type": "directory"},
            },
        },
    }
    if include_statistics:
        statistics = {
            "run_args": {"command": command},
            "input_volumes": {
                "data_path": {"mount_path": "/data", "type": "directory"},
            },
        }
        if include_statistics_output:
            statistics["output_volumes"] = {
                "output_path": {
                    "mount_path": "/statistics.yaml",
                    "type": "file",
                }
            }
        tasks["statistics"] = statistics
    if extra_tasks:
        tasks.update(extra_tasks)
    return {
        "container_type": "DockerImage",
        "image": "example/preparator:latest",
        "tasks": tasks,
    }


def test_valid_prepare_and_statistics_tasks_pass():
    parser = SimpleContainerParser(_preparator_config(), ["docker"])
    parser.check_schema()


def test_preparator_requires_statistics_task():
    parser = SimpleContainerParser(
        _preparator_config(include_statistics=False), ["docker"]
    )
    with pytest.raises(InvalidContainerSpec, match="statistics"):
        parser.check_schema()


def test_preparator_rejects_separate_sanity_check_task():
    parser = SimpleContainerParser(
        _preparator_config(
            extra_tasks={
                "sanity_check": {
                    "run_args": {"command": "echo"},
                    "input_volumes": {
                        "data_path": {"mount_path": "/data", "type": "directory"},
                    },
                }
            }
        ),
        ["docker"],
    )
    with pytest.raises(InvalidContainerSpec, match="sanity_check"):
        parser.check_schema()


def test_preparator_rejects_legacy_check_no_prepare_task():
    parser = SimpleContainerParser(
        _preparator_config(
            include_statistics=False,
            extra_tasks={
                "check_no_prepare": {
                    "run_args": {
                        "command": "python3 -m prep_workflow.main --start=sanity_check"
                    },
                    "input_volumes": {
                        "data_path": {"mount_path": "/data", "type": "directory"},
                    },
                    "output_volumes": {
                        "output_path": {
                            "mount_path": "/statistics.yaml",
                            "type": "file",
                        }
                    },
                }
            },
        ),
        ["docker"],
    )
    with pytest.raises(InvalidContainerSpec, match="statistics"):
        parser.check_schema()


def test_statistics_command_must_start_at_sanity_check():
    parser = SimpleContainerParser(
        _preparator_config(command="python3 -m prep_workflow.main"), ["docker"]
    )
    with pytest.raises(InvalidContainerSpec, match="--start=sanity_check"):
        parser.check_schema()


def test_statistics_command_list_form_is_accepted():
    parser = SimpleContainerParser(
        _preparator_config(
            command=[
                "python3",
                "-m",
                "prep_workflow.main",
                "--start=sanity_check",
            ]
        ),
        ["docker"],
    )
    parser.check_schema()


def test_statistics_requires_output_path_for_statistics_file():
    parser = SimpleContainerParser(
        _preparator_config(include_statistics_output=False), ["docker"]
    )
    with pytest.raises(InvalidContainerSpec, match="output_path"):
        parser.check_schema()


def test_model_container_skips_preparator_constraints():
    config = {
        "container_type": "DockerImage",
        "image": "example/model:latest",
        "tasks": {
            "infer": {
                "run_args": {"command": "infer"},
                "input_volumes": {
                    "data_path": {"mount_path": "/data", "type": "directory"},
                },
                "output_volumes": {
                    "output_path": {"mount_path": "/out", "type": "directory"},
                },
            }
        },
    }
    parser = SimpleContainerParser(config, ["docker"])
    parser.check_schema()
