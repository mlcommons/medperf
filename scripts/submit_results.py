import argparse
import medperf
from medperf import config
from medperf.entities.result import Result
from medperf.ui.factory import UIFactory
from medperf.comms.factory import CommsFactory
from medperf.commands.result.submit import ResultSubmission


def setup():
    config.ui = UIFactory.create_ui("CLI")
    config.comms = CommsFactory.create_comms("REST", config.ui, config.server)

    return config.ui, config.comms


def get_results(benchmark_uid: int):
    # Get all local results
    all_results = Result.all(config.ui)
    results = []
    for result in all_results:
        is_test = not result.benchmark_uid.isdigit()
        is_submitted = result.uid is not None
        # Filter out temporary or submitted results
        if is_test or is_submitted:
            continue
        # Filter out unrelated_results
        if int(result.benchmark_uid) == benchmark_uid:
            results.append(result)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Submit results for a specific benchmark"
    )
    parser.add_argument(
        "-b",
        "--benchmark",
        nargs="?",
        default=5,
        type=int,
        help="Benchmark UID. Defaults to 5",
    )
    parser.add_argument(
        "-y",
        "--autoapprove",
        dest="approve",
        action="store_true",
        help="Skip approval step. Automatically submits all results.",
    )
    log_file = medperf.utils.storage_path(config.log_file)
    medperf.utils.setup_logs("DEBUG", log_file)
    parser.set_defaults(approve=False)
    args = parser.parse_args()
    in_config = vars(args)

    setup()
    benchmark_uid = int(in_config["benchmark"])
    approved = in_config["approve"]
    if approved:
        print(
            "Skip approvals has been set to TRUE. Doing batch submission without requesting separate approvals"
        )
    results = get_results(benchmark_uid)
    for result in results:
        benchmark_uid = result.benchmark_uid
        data_uid = result.dataset_uid
        model_uid = result.model_uid
        print(
            f"Initiating result submission for {benchmark_uid}_{model_uid}_{data_uid}"
        )
        try:
            sub = ResultSubmission(
                benchmark_uid,
                data_uid,
                model_uid,
                config.comms,
                config.ui,
                approved=approved,
            )
            sub.upload_results()
        except (Exception, SystemExit):
            print("Result submission failed or was cancelled")
