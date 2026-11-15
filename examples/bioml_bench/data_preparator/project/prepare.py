"""Prepares a BioML-bench task with the task's own prepare.py: the public files
(what an agent sees) become the MedPerf data, the private files (the answers)
become the MedPerf labels."""

import shutil
import tempfile
from pathlib import Path

from biomlbench_task import (
    POLARIS_BENCHMARK_DIR,
    get_task,
    read_task_id,
    restore_raw_dir,
    use_local_polaris_benchmark,
)

RAW_DATA_PATH = "/mlcommons/volumes/raw_data"
PARAMETERS_PATH = "/mlcommons/volumes/parameters/parameters_file.yaml"
DATA_PATH = Path("/mlcommons/volumes/data")
LABELS_PATH = Path("/mlcommons/volumes/labels")


def main():
    task_id = read_task_id(PARAMETERS_PATH)
    with tempfile.TemporaryDirectory() as data_dir:
        task = get_task(task_id, data_dir)
        restore_raw_dir(task, RAW_DATA_PATH)
        if task.data_source["type"] == "polaris":
            benchmark_dir = task.raw_dir / POLARIS_BENCHMARK_DIR
            use_local_polaris_benchmark(task, benchmark_dir)
            # grade.py loads the benchmark too, so the evaluator gets a copy
            shutil.copytree(benchmark_dir, LABELS_PATH / POLARIS_BENCHMARK_DIR, dirs_exist_ok=True)

        task.prepare_fn(raw=task.raw_dir, public=DATA_PATH, private=LABELS_PATH)

    # what `biomlbench prepare` adds after prepare.py: the task description
    (DATA_PATH / "description.md").write_text(task.description)


if __name__ == "__main__":
    main()
