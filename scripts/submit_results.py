import argparse
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
    results = Result.all(config.ui)
    # Filter out results that are not related to the current benchmark
    results = [
        result for result in results if int(result.benchmark_uid) == benchmark_uid
    ]
    results = [result for result in results if result.uid is None]
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
