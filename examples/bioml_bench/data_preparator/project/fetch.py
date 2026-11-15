"""Downloads a BioML-bench task's public data and writes the files needed to run
it on MedPerf. Runs with network access, outside MedPerf (see fetch_task.sh):

    <out>/raw/data/                     the raw dataset: what BioML-bench downloads
    <out>/raw/labels/                   empty: the answers are split out of the raw
                                        data by the data preparator
    <out>/demo_data.tar.gz              the raw dataset plus paths.yaml, used as the
                                        benchmark's demo dataset
    <out>/metrics_additional_files.tar.gz
                                        the task's leaderboard, if it can be fetched
    <out>/parameters.yaml               the task id, for the preparator and evaluator
"""

import argparse
import os
import shutil
import tarfile
import tempfile

import yaml

from biomlbench_task import POLARIS_BENCHMARK_DIR, SHARED_DIR, get_task, shared_dir


def copy_raw_data(task, raw_data_path):
    shutil.copytree(task.raw_dir, raw_data_path, dirs_exist_ok=True)
    # files shared by all the tasks of the source, e.g. ProteinGym's metadata.
    # Archives and extracted folders are left out: the task's own file was
    # already copied into its raw folder
    shared_files = [
        entry
        for entry in os.scandir(shared_dir(task))
        if entry.is_file() and not entry.name.endswith(".zip")
    ]
    if shared_files:
        os.makedirs(os.path.join(raw_data_path, SHARED_DIR), exist_ok=True)
        for entry in shared_files:
            shutil.copy(entry.path, os.path.join(raw_data_path, SHARED_DIR, entry.name))


def save_polaris_benchmark(task, raw_data_path):
    import polaris

    benchmark = polaris.load_benchmark(task.data_source["benchmark_id"])
    benchmark.to_json(os.path.join(raw_data_path, POLARIS_BENCHMARK_DIR))


def save_leaderboard(data_source, task, out):
    try:
        leaderboard = data_source.get_leaderboard(task.data_source)
    except Exception as e:
        print(f"Could not fetch the leaderboard, results will not be ranked: {e}")
        return
    with tempfile.TemporaryDirectory() as tmp:
        leaderboard.to_csv(os.path.join(tmp, "leaderboard.csv"), index=False)
        with tarfile.open(os.path.join(out, "metrics_additional_files.tar.gz"), "w:gz") as tar:
            tar.add(os.path.join(tmp, "leaderboard.csv"), arcname="leaderboard.csv")
    print(f"Saved a leaderboard of {len(leaderboard)} entries")


def make_demo_tarball(out):
    with tempfile.TemporaryDirectory() as tmp:
        paths_file = os.path.join(tmp, "paths.yaml")
        with open(paths_file, "w") as f:
            yaml.safe_dump({"data_path": "raw/data", "labels_path": "raw/labels"}, f)
        with tarfile.open(os.path.join(out, "demo_data.tar.gz"), "w:gz") as tar:
            tar.add(paths_file, arcname="paths.yaml")
            tar.add(os.path.join(out, "raw"), arcname="raw")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--task", required=True, help="BioML-bench task id, e.g. polarishub/tdcommons-caco2-wang")
    parser.add_argument("--out", required=True, help="Output folder")
    args = parser.parse_args()

    from biomlbench.data_sources import DataSourceFactory

    with tempfile.TemporaryDirectory() as data_dir:
        task = get_task(args.task, data_dir)
        data_source = DataSourceFactory.create(task.data_source["type"])
        task.raw_dir.mkdir(parents=True)
        print(f"Downloading {args.task}")
        data_source.download(task.data_source, task.raw_dir)

        raw_data_path = os.path.join(args.out, "raw", "data")
        shutil.rmtree(os.path.join(args.out, "raw"), ignore_errors=True)
        os.makedirs(os.path.join(args.out, "raw", "labels"))
        # keeps the empty labels folder in git
        open(os.path.join(args.out, "raw", "labels", ".gitkeep"), "w").close()
        copy_raw_data(task, raw_data_path)
        if task.data_source["type"] == "polaris":
            save_polaris_benchmark(task, raw_data_path)
        save_leaderboard(data_source, task, args.out)

    make_demo_tarball(args.out)
    with open(os.path.join(args.out, "parameters.yaml"), "w") as f:
        yaml.safe_dump({"task_id": args.task}, f)
    print(f"{args.task} is ready in {args.out}")


if __name__ == "__main__":
    main()
