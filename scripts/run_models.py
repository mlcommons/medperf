import os
import re
import json
import shutil

import medperf
import argparse
from medperf import config
from medperf.entities.result import Result
from medperf.entities.dataset import Dataset
from medperf.ui.factory import UIFactory
from medperf.comms.factory import CommsFactory
from medperf.commands.result.create import BenchmarkExecution
from medperf.commands.compatibility_test import CompatibilityTestExecution

config.platform = "singularity"

VALID_DRIVER_MAJOR_VERSION = 450
VALID_DRIVER_MINOR_VERSION = 51
VALID_SINGULARITY_VERSION = "3.9.5"


def setup():
    config.ui = UIFactory.create_ui("CLI")
    config.comms = CommsFactory.create_comms("REST", config.ui, config.server)

    return config.ui, config.comms


def validate_setup():
    # Get nvidia driver version
    driver_stream = os.popen("nvidia-smi")
    driver_output = driver_stream.read()
    driver_version_search = re.search(
        r"Driver Version: (\d*).(\d*).(\d*)", driver_output
    )
    driver_major_version = int(driver_version_search[1])
    driver_minor_version = int(driver_version_search[2])

    # Get Singularity version
    singularity_stream = os.popen("singularity version")
    singularity_output = singularity_stream.read()
    singularity_version = singularity_output.strip()

    # Assert correct versions are installed
    driver_check = (
        driver_major_version >= VALID_DRIVER_MAJOR_VERSION
        and driver_minor_version >= VALID_DRIVER_MINOR_VERSION
    )
    driver_error_msg = f"Your installed NVIDIA Driver doesn't match the expected driver version >= {VALID_DRIVER_MAJOR_VERSION}.{VALID_DRIVER_MINOR_VERSION}"
    assert driver_check, driver_error_msg

    singularity_check = singularity_version == VALID_SINGULARITY_VERSION
    singularity_error_msg = f"Your installed Singularity version doesn't match the expected version: {VALID_SINGULARITY_VERSION}"
    assert singularity_check, singularity_error_msg


def get_models_to_run(models_file, ui, comms):
    cubes = comms.get_cubes()
    results = Result.all(ui)
    results = [result.todict() for result in results]
    executed_models = set([int(result["model"]) for result in results])
    cubes_names_dict = {cube["name"]: cube for cube in cubes}

    with open(models_file, "r") as f:
        models_names = json.load(f)

    models_cubes = [
        cubes_names_dict[name] for name in models_names if name in cubes_names_dict
    ]
    models_ids = [
        (cube["name"], cube["id"])
        for cube in models_cubes
        if cube["id"] not in executed_models
    ]
    return models_ids


def get_dset(data_uid, ui):
    dsets = Dataset.all(ui)
    assert len(dsets) > 0, "There is no dataset to use. Please prepare a dataset"
    if data_uid is None:
        assert (
            len(dsets) == 1
        ), "Can't infer a dataset to use. Please provide a dataset UID"
        return dsets[0]
    for dset in dsets:
        if dset.generated_uid == data_uid:
            return dset


def cleanup_stale_predictions(model_id, data_uid):
    preds_path = medperf.utils.storage_path(config.predictions_storage)
    stale_path = os.path.join(preds_path, str(model_id), data_uid)
    if os.path.exists(stale_path):
        # Found a stale predictions path. Remove it
        print(f"Removing leftover predictions path: {stale_path}")
        shutil.rmtree(stale_path)


def main(benchmark_uid, data_uid, timeout, models_file, test=False, cleanup=False):
    config.infer_timeout = timeout
    log_file = medperf.utils.storage_path(config.log_file)
    medperf.utils.setup_logs("DEBUG", log_file)
    validate_setup()
    ui, comms = setup()
    models_ids = get_models_to_run(models_file, ui, comms)
    data = get_dset(data_uid, ui)
    local_uid = data.registration["generated_uid"]
    cubes_path = medperf.utils.storage_path(config.cubes_storage)
    for model_name, model_id in models_ids:
        if test:
            print("Running tests to ensure execution works")
            CompatibilityTestExecution.run(benchmark_uid, comms, ui, model=model_id)
            print("Done!")
        print(f"Initiating Benchmark Execution with model {model_name}")
        cleanup_stale_predictions(model_id, local_uid)
        try:
            BenchmarkExecution.run(benchmark_uid, local_uid, model_id, comms, ui)
            if cleanup:
                model_path = os.path.join(cubes_path, str(model_id))
                print(f"Removing downloaded model at {model_path}")
                shutil.rmtree(model_path)
        except (Exception, SystemExit):
            print(f"Benchmark execution with model {model_id} failed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run medperf's benchmark over a batch of models"
    )
    parser.add_argument(
        "-b",
        "--benchmark",
        nargs="?",
        default=2,
        type=int,
        help="Benchmark UID. Defaults to 2",
    )
    parser.add_argument(
        "-d",
        "--data-uid",
        nargs="?",
        type=str,
        help="Dataset UID. If not provided and only one dataset exists then that one will be used instead",
    )
    parser.add_argument(
        "-n", "--num-cases", type=int, help="Number of cases inside the dataset"
    )
    parser.add_argument(
        "-t",
        "--time-case",
        nargs="?",
        default=10 * 60,
        type=int,
        help="Expected processing time per case. Defaults to 10 minutes",
    )
    parser.add_argument(
        "-m",
        "--models-file",
        nargs="?",
        default="fets_subm_list.json",
        type=str,
        help="Path to JSON document containing a list of model names in priority order",
    )
    parser.add_argument(
        "--no-test",
        action="store_false",
        help="Skip approval step. Automatically submits all results.",
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_false",
        help="Remove models after model execution. This could save up space, but might cause redownloading models in case of multiple executions",
    )
    args = parser.parse_args()
    in_config = vars(args)

    benchmark_uid = in_config["benchmark"]
    data_uid = in_config["data_uid"]
    timeout = in_config["num_cases"] * in_config["time_case"]
    models_file = in_config["models_file"]
    test = in_config["no_test"]
    cleanup = in_config["no_cleanup"]

    main(benchmark_uid, data_uid, timeout, models_file, test=test, cleanup=cleanup)
