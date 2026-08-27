"""Shared helpers for Web UI end-to-end tests."""

from __future__ import annotations

import logging
import shutil
import urllib.request
from pathlib import Path
from typing import Optional, Union

import yaml

from medperf.exceptions import ExecutionError
from medperf.utils import remove_path, untar
from medperf.web_ui.tests import config as tests_config

_CHESTXRAY_TRAIN_SAMPLE_URL = (
    "https://storage.googleapis.com/medperf-storage/chestxray_train_sample1.tar.gz"
)
_ARCHIVE_NAME = "chestxray_train_sample1.tar.gz"
_INNER_DIR = "chestxray_train_sample1"


def _repo_root() -> Path:
    # cli/medperf/web_ui/tests/e2e/helpers.py -> parents[5] == repository root
    return Path(__file__).resolve().parents[5]


def _download_url_to_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response, open(destination, "wb") as out_file:
        shutil.copyfileobj(response, out_file)


def prepare_chestxray_train_sample_data(
    dest_dir: Optional[Union[str, Path]] = None,
    *,
    overwrite: bool = False,
) -> Path:
    """Download ``chestxray_train_sample1.tar.gz`` and produce ``col1`` and ``col2``.

    Same end result as ``cli/cli_tests_training.sh`` (wget, tar, rename). Runs
    synchronously until download, extraction, and moves complete.

    Default ``dest_dir`` is ``<repo>/examples/chestxray_train_sample_data``.

    Args:
        dest_dir: Directory that will contain ``col1`` and ``col2``.
        overwrite: Remove existing ``col1``, ``col2``, and extracted tree first.

    Returns:
        Resolved ``dest_dir``.
    """
    if dest_dir is None:
        dest_dir = _repo_root() / "examples" / "chestxray_train_sample_data"

    dest = Path(dest_dir).expanduser().resolve()
    dest.mkdir(parents=True, exist_ok=True)

    col1 = dest / "col1"
    col2 = dest / "col2"
    inner = dest / _INNER_DIR

    if col1.is_dir() and col2.is_dir() and not overwrite:
        logging.info(
            "Chest X-ray train sample already present (%s, %s); skipping download.",
            col1,
            col2,
        )
        return dest

    if overwrite:
        for path in (col1, col2, inner):
            if path.exists():
                remove_path(str(path))

    archive = dest / _ARCHIVE_NAME
    logging.info("Downloading %s -> %s", _CHESTXRAY_TRAIN_SAMPLE_URL, archive)
    _download_url_to_file(_CHESTXRAY_TRAIN_SAMPLE_URL, archive)

    untar(str(archive), remove=True, extract_to=str(dest))

    dataset_1 = inner / "dataset_1"
    dataset_2 = inner / "dataset_2"
    if not dataset_1.is_dir() or not dataset_2.is_dir():
        raise ExecutionError(
            "Unexpected archive layout: expected "
            f"{dataset_1} and {dataset_2} after extracting {_ARCHIVE_NAME!r}"
        )

    shutil.move(str(dataset_1), str(col1))
    shutil.move(str(dataset_2), str(col2))

    if inner.is_dir():
        remove_path(str(inner))

    logging.info("Prepared training sample: %s and %s", col1, col2)
    return dest


def write_training_participants_yaml_for_e2e() -> str:
    """Create ``examples/training_participants_e2e.yaml`` for training start-event.

    Keys/values are dataset-owner emails from ``tests.config`` so participants
    match the accounts used in the training workflow E2E.
    """
    rel = Path("examples") / "training_participants_e2e.yaml"
    path = _repo_root() / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        tests_config.DSET_OWNER_EMAIL: tests_config.DSET_OWNER_EMAIL,
        tests_config.DSET_OWNER2_EMAIL: tests_config.DSET_OWNER2_EMAIL,
    }
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
    return rel.as_posix()


def ensure_training_event_report_yaml_stub_dict():
    # This is needed to ensure the event can be closed after stopping the aggregator, as the code expects a report.yaml
    # to be present. We overwrite it with an empty dict, as the test does not rely on any of the report content.
    # This should be fixed soon #TODO
    """Overwrite newest ``.../report<timestamp>/report.yaml`` under the fixed E2E path."""
    training_root = Path.home() / ".medperf" / "training_events" / "localhost_8000"

    candidates: list[Path] = []
    for path in training_root.rglob("report.yaml"):
        if path.is_file() and path.parent.name.startswith("report"):
            candidates.append(path)

    if not candidates:
        raise ExecutionError(
            f"No report.yaml under a report* folder under {training_root}"
        )

    target = max(candidates, key=lambda p: p.stat().st_mtime)
    with open(target, "w", encoding="utf-8") as f:
        yaml.safe_dump({}, f, default_flow_style=False)
    return str(target)
