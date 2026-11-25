"""Runs BioML-bench task code (prepare.py, grade.py) without network access.

BioML-bench keeps each task's files in a cache folder:

    <data_dir>/<source>/<task>/raw/       what the data source downloaded
    <data_dir>/<source>/                  files shared by all the tasks of a source

fetch.py exports the raw folder as a MedPerf raw dataset, with the shared files
under `shared/`. This module rebuilds that layout so the task code finds its files.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path

import yaml

SHARED_DIR = "shared"
POLARIS_BENCHMARK_DIR = "polaris_benchmark"
SUPPORTED_SOURCES = ["polaris", "proteingym-dms"]


def read_task_id(parameters_path):
    with open(parameters_path) as f:
        return yaml.safe_load(f)["task_id"]


def get_task(task_id, data_dir):
    from biomlbench.registry import Registry

    task = Registry(Path(data_dir)).get_task(task_id)
    source_type = task.data_source["type"]
    if source_type not in SUPPORTED_SOURCES:
        raise ValueError(
            f"Task {task_id} gets its data from '{source_type}'. "
            f"Supported sources: {', '.join(SUPPORTED_SOURCES)}"
        )
    return task


def shared_dir(task):
    return task.raw_dir.parent.parent


def restore_raw_dir(task, raw_data_path):
    """Copies a raw dataset exported by fetch.py back into BioML-bench's layout."""
    task.raw_dir.mkdir(parents=True, exist_ok=True)
    for name in os.listdir(raw_data_path):
        source = os.path.join(raw_data_path, name)
        if name == SHARED_DIR:
            shutil.copytree(source, shared_dir(task), dirs_exist_ok=True)
        elif os.path.isdir(source):
            shutil.copytree(source, task.raw_dir / name)
        else:
            shutil.copy(source, task.raw_dir / name)


def relocate_polaris_benchmark(benchmark_dir, out_dir):
    """benchmark.to_json() records absolute paths to the dataset files, which
    change once the files are mounted elsewhere. Writes copies of the JSON files
    to out_dir with the paths pointing into benchmark_dir."""
    benchmark_dir = os.path.abspath(benchmark_dir)
    with open(os.path.join(benchmark_dir, "benchmark.json")) as f:
        benchmark = json.load(f)
    dataset_file = os.path.basename(benchmark["dataset"])
    with open(os.path.join(benchmark_dir, dataset_file)) as f:
        dataset = json.load(f)

    for key in ["table", "zarr_root_path"]:
        if dataset.get(key):
            dataset[key] = os.path.join(benchmark_dir, os.path.basename(dataset[key]))
    benchmark["dataset"] = os.path.join(out_dir, dataset_file)

    with open(benchmark["dataset"], "w") as f:
        json.dump(dataset, f)
    benchmark_path = os.path.join(out_dir, "benchmark.json")
    with open(benchmark_path, "w") as f:
        json.dump(benchmark, f)
    return benchmark_path


def use_local_polaris_benchmark(task, benchmark_dir):
    """Polaris tasks call po.load_benchmark(<Hub id>) in prepare.py and grade.py.
    This makes the call load the copy saved by fetch.py instead of the Hub."""
    import polaris

    benchmark_id = task.data_source["benchmark_id"]
    load_benchmark = polaris.load_benchmark

    def load_local_benchmark(path, *args, **kwargs):
        if path != benchmark_id:
            raise ValueError(f"Only {benchmark_id} is available offline, got {path}")
        with tempfile.TemporaryDirectory() as tmp:
            return load_benchmark(relocate_polaris_benchmark(benchmark_dir, tmp), *args, **kwargs)

    polaris.load_benchmark = load_local_benchmark
