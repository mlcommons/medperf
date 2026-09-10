"""The prepared dataset: what the three tasks agree it looks like.

The benchmark script reads this same file, from its own container -- see
`benchmark/connection.py`. The filename and the keys below are the contract
between them, and changing one without the other is the failure this module
exists to make obvious.

There are no prompts here, and no labels. The prompts belong to the benchmark
service; what a data owner registers is the connection that reaches theirs.
"""

import os

import yaml

FILENAME = "connection.yaml"

# The data owner's half: their service and their account.
OWNER_FIELDS = ("url", "key", "model_id")

# The benchmark owner's half, from the preparation parameters. What shape of
# run to ask the service for -- not the operator's to choose, and not the data
# owner's either.
PARAMETER_FIELDS = ("benchmark_type", "mode", "locale")

BENCHMARK_TYPES = ("general", "security")
MODES = ("test", "short", "full", "official")
LOCALES = ("en_us", "fr_fr")

# `labels/` cannot be empty: MedPerf hashes `data/` and `labels/` together into
# the dataset's identity, and a confidential run's policy binds to that hash.
LABELS_NOTE = (
    "This benchmark has no labels. The benchmark service holds the prompts,\n"
    "runs the annotators and computes the grades; the workload answers prompts\n"
    "and nothing else. See ../data/connection.yaml.\n"
)
LABELS_FILE = "NO_LABELS.txt"


def read_owner_settings(raw_path: str) -> dict:
    path = os.path.join(raw_path, FILENAME)
    if not os.path.exists(path):
        raise RuntimeError(
            f"No {FILENAME} in {raw_path}. This benchmark's dataset is a"
            f" {FILENAME} naming the benchmark service and the key that reaches"
            " it -- see the example under demo/raw/."
        )
    with open(path) as f:
        described = yaml.safe_load(f) or {}

    for field in ("url", "key"):
        if not described.get(field):
            raise RuntimeError(f"{path} is missing {field}")

    unknown = set(described) - set(OWNER_FIELDS)
    if unknown:
        raise RuntimeError(
            f"{path} has fields that are not a data owner's to set:"
            f" {', '.join(sorted(unknown))}"
        )
    return {field: described[field] for field in OWNER_FIELDS if field in described}


def read_run_shape(parameters: dict) -> dict:
    shape = {
        field: str(parameters[field]).strip().lower()
        for field in PARAMETER_FIELDS
        if parameters.get(field)
    }
    _check(shape.get("benchmark_type"), BENCHMARK_TYPES, "benchmark_type")
    _check(shape.get("mode"), MODES, "mode")
    _check(shape.get("locale"), LOCALES, "locale")
    return shape


def _check(value, allowed, name) -> None:
    if value is not None and value not in allowed:
        raise RuntimeError(f"{name} must be one of {', '.join(allowed)}, not {value!r}")


def write(output_path: str, output_labels_path: str, settings: dict) -> None:
    """Writes the pair of folders, in a fixed order.

    Sorted keys, because MedPerf hashes these two folders into the dataset's
    identity. Preparing the same connection twice has to produce the same
    bytes."""
    with open(os.path.join(output_path, FILENAME), "w") as f:
        yaml.safe_dump(settings, f, sort_keys=True)

    with open(os.path.join(output_labels_path, LABELS_FILE), "w") as f:
        f.write(LABELS_NOTE)


def read(data_path: str, labels_path: str) -> dict:
    with open(os.path.join(data_path, FILENAME)) as f:
        return yaml.safe_load(f) or {}
