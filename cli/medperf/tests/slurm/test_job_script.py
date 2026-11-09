import shlex

import pytest

from medperf.exceptions import InvalidArgumentError
from medperf.slurm import job_script
from medperf.slurm.job_script import (
    EXIT_PATH_NOT_VISIBLE,
    EXIT_RUNTIME_NOT_FOUND,
    parse_extra_args,
    render_job_script,
    resource_directives,
    validate_resources,
)

JOB_DIR = "/shared/medperf/slurm_jobs/job1"
COMMAND = [
    "apptainer",
    "run",
    "-eC",
    "--bind",
    "/shared/data:/mlcommons/volumes/data:ro",
    "--bind",
    "/shared/preds:/mlcommons/volumes/output",
    "/shared/images/model.sif",
    "infer",
]


def render(**kwargs):
    defaults = dict(command=COMMAND, job_dir=JOB_DIR, task="infer")
    defaults.update(kwargs)
    return render_job_script(**defaults)


@pytest.mark.parametrize("time", ["90", "30:00", "02:00:00", "1-00", "1-12:00", "2-00:00:00"])
def test_validate_resources_accepts_slurm_time_formats(time):
    validate_resources(time=time)


@pytest.mark.parametrize("time", ["2h", "02:00:00\n#SBATCH --x", "1 day", "-1", ""])
def test_validate_resources_rejects_bad_time(time):
    with pytest.raises(InvalidArgumentError):
        validate_resources(time=time)


@pytest.mark.parametrize("mem", ["64G", "512M", "0", "1024", "2t"])
def test_validate_resources_accepts_memory(mem):
    validate_resources(mem=mem)


@pytest.mark.parametrize("mem", ["64 G", "64GB", "lots", "1G\n#SBATCH --x"])
def test_validate_resources_rejects_bad_memory(mem):
    with pytest.raises(InvalidArgumentError):
        validate_resources(mem=mem)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"partition": "booster ; rm"},
        {"partition": "a\nb"},
        {"account": "my account"},
        {"gres": "gpu: 4"},
        {"cpus_per_task": 0},
        {"cpus_per_task": True},
    ],
)
def test_validate_resources_rejects_unsafe_values(kwargs):
    with pytest.raises(InvalidArgumentError):
        validate_resources(**kwargs)


def test_resource_directives_only_include_configured_values():
    # Act
    directives = resource_directives(partition="booster", time="01:00:00")

    # Assert
    assert directives == [
        "#SBATCH --nodes=1",
        "#SBATCH --ntasks=1",
        "#SBATCH --partition=booster",
        "#SBATCH --time=01:00:00",
    ]


def test_resource_directives_all_values():
    # Act
    directives = resource_directives(
        partition="booster",
        account="myproj",
        time="2-00:00:00",
        cpus_per_task=72,
        mem="0",
        gres="gpu:4",
    )

    # Assert
    assert "#SBATCH --account=myproj" in directives
    assert "#SBATCH --cpus-per-task=72" in directives
    assert "#SBATCH --mem=0" in directives
    assert "#SBATCH --gres=gpu:4" in directives


def test_parse_extra_args_splits_like_a_shell():
    assert parse_extra_args('--qos=normal --comment "two words"') == [
        "--qos=normal",
        "--comment",
        "two words",
    ]


def test_parse_extra_args_empty():
    assert parse_extra_args(None) == []
    assert parse_extra_args("") == []


@pytest.mark.parametrize(
    "extra", ["--output=/x", "-o /x", "--wrap='hostname'", "--job-name=x", "--parsable"]
)
def test_parse_extra_args_rejects_options_managed_by_medperf(extra):
    with pytest.raises(InvalidArgumentError):
        parse_extra_args(extra)


def test_parse_extra_args_rejects_unbalanced_quotes():
    with pytest.raises(InvalidArgumentError):
        parse_extra_args('--comment "unterminated')


def test_job_script_has_directives_before_any_command():
    # Arrange
    directives = resource_directives(partition="booster", gres="gpu:4")

    # Act
    script = render(directives=directives)

    # Assert
    lines = script.splitlines()
    assert lines[0] == "#!/bin/bash"
    first_command = next(
        i for i, line in enumerate(lines) if line and not line.startswith("#")
    )
    sbatch_lines = [i for i, line in enumerate(lines) if line.startswith("#SBATCH")]
    # sbatch stops reading directives at the first command
    assert max(sbatch_lines) < first_command
    assert "#SBATCH --gres=gpu:4" in lines
    assert f"#SBATCH --output={JOB_DIR}/job.log" in lines
    assert f"#SBATCH --chdir={JOB_DIR}" in lines
    assert "#SBATCH --job-name=medperf-infer" in lines
    assert "#SBATCH --no-requeue" in lines


def test_job_script_runs_the_exact_container_command():
    # Act
    script = render()

    # Assert
    command_line = next(
        line for line in script.splitlines() if line.startswith("apptainer ")
    )
    assert shlex.split(command_line) == COMMAND


def test_job_script_quotes_hostile_arguments():
    # Arrange
    command = ["apptainer", "exec", "/img.sif", "echo", "a b", "$(id)", "it's", "`x`", ";"]

    # Act
    script = render(command=command)

    # Assert
    command_line = next(
        line for line in script.splitlines() if line.startswith("apptainer ")
    )
    assert shlex.split(command_line) == command


def test_job_script_checks_bind_sources_and_image_are_visible():
    # Act
    script = render(paths_to_check=["/shared/images/model.sif"])

    # Assert
    loop = next(line for line in script.splitlines() if line.startswith("for path in"))
    checked = shlex.split(loop[len("for path in ") : -len("; do")])  # noqa
    assert checked == ["/shared/images/model.sif", "/shared/data", "/shared/preds"]
    assert f"medperf_finish {EXIT_PATH_NOT_VISIBLE}" in script


def test_job_script_checks_runtime_on_compute_node():
    script = render()
    assert "if ! command -v apptainer" in script
    assert f"medperf_finish {EXIT_RUNTIME_NOT_FOUND}" in script


def test_job_script_exports_container_environment_safely():
    # Act
    script = render(env={"SINGULARITYENV_MSG": "hello $USER; rm -rf ~"})

    # Assert
    assert "export SINGULARITYENV_MSG='hello $USER; rm -rf ~'" in script


def test_job_script_rejects_invalid_environment_names():
    with pytest.raises(InvalidArgumentError):
        render(env={"BAD-NAME": "x"})
    with pytest.raises(InvalidArgumentError):
        render(env={"X=1; rm": "x"})


@pytest.mark.parametrize("job_dir", ["relative/dir", "/with space/dir", "/odd%j/dir"])
def test_job_script_rejects_unusable_job_dirs(job_dir):
    with pytest.raises(InvalidArgumentError):
        render(job_dir=job_dir)


def test_job_script_gpu_forwarding_is_optional():
    assert "CUDA_VISIBLE_DEVICES" not in render()
    script = render(forward_gpu_visibility=True)
    assert 'export SINGULARITYENV_CUDA_VISIBLE_DEVICES="$CUDA_VISIBLE_DEVICES"' in script


def test_job_script_includes_setup_commands_before_checks():
    # Act
    script = render(setup_commands="module load Stages/2025\nmodule load CUDA\n")

    # Assert
    assert script.index("module load CUDA") < script.index("command -v apptainer")


def test_job_script_records_exit_code_atomically():
    script = render()
    assert 'mv "$EXIT_CODE_FILE.tmp" "$EXIT_CODE_FILE"' in script
    assert script.rstrip().endswith('medperf_finish "$rc"')


def test_job_name_sanitizes_task():
    assert job_script.job_name_for_task("run script/x") == "medperf-run_script_x"


@pytest.mark.parametrize(
    "arch,expected",
    [
        ("x86_64", "amd64"),
        ("amd64", "amd64"),
        ("aarch64", "arm64"),
        ("arm64", "arm64"),
        ("i686", "386"),
        ("armv7l", "arm"),
        ("ppc64le", "ppc64le"),
        ("  AARCH64\n", "arm64"),
        ("", None),
        (None, None),
    ],
)
def test_normalize_arch(arch, expected):
    assert job_script.normalize_arch(arch) == expected


def test_job_script_checks_node_architecture_before_container():
    # Act
    script = render(image_arch="aarch64")

    # Assert
    assert "node_arch=$(uname -m)" in script
    assert 'if [ "$node_arch" != arm64 ]; then' in script
    assert f"medperf_finish {job_script.EXIT_ARCH_MISMATCH}" in script
    assert script.index("node_arch=$(uname -m)") < script.index("apptainer run")


def test_job_script_without_known_architecture_skips_the_check():
    assert "uname -m" not in render()


def test_job_script_rejects_unsafe_architecture_values():
    with pytest.raises(InvalidArgumentError):
        render(image_arch="amd64; rm -rf ~")
