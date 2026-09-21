"""Container entrypoint.

One executable drives the preparator through an optional start argument:

* no argument               -> run preparation steps only (first workflow step)
* ``--start=sanity_check``  -> start at the step whose ``id`` is ``sanity_check``

Starts are conventional: preparation begins at the first step; validation begins
at step id ``sanity_check``.

Mount locations default to the standard MedPerf volume paths and can be overridden
via environment variables (handy for tests).
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import Dict, Tuple

from prep_workflow.base import Condition, Paths, Step
from prep_workflow.builtins import builtin_steps
from prep_workflow.context import ContextFactory
from prep_workflow.discovery import add_to_path, discover_conditions, discover_steps
from prep_workflow.engine import Engine
from prep_workflow.graph import Graph, PREPARE_START, SANITY_CHECK_START, WorkflowError
from prep_workflow.report import Report

STARTS = (PREPARE_START, SANITY_CHECK_START)
SANITY_CHECK_STEP = "SanityCheck"
STATISTICS_STEP = "Statistics"

_DEFAULTS = {
    "PROJECT_DIR": "/project",
    "WORKFLOW_YAML": "/project/workflow.yaml",
    "INPUT_DATA": "/mlcommons/volumes/raw_data",
    "INPUT_LABELS": "/mlcommons/volumes/raw_labels",
    "OUTPUT_DATA": "/mlcommons/volumes/data",
    "OUTPUT_LABELS": "/mlcommons/volumes/labels",
    "METADATA": "/mlcommons/volumes/metadata",
    "REPORT_FILE": "/mlcommons/volumes/report/report.yaml",
    "PARAMETERS_FILE": "/mlcommons/volumes/parameters/parameters_file.yaml",
    "ADDITIONAL_FILES": "/mlcommons/volumes/additional_files",
    "STATISTICS_FILE": "/mlcommons/volumes/statistics/statistics.yaml",
}


def _env(key: str) -> str:
    return os.environ.get(key, _DEFAULTS[key])


def build_paths() -> Paths:
    return Paths(
        input_data=_env("INPUT_DATA"),
        input_labels=_env("INPUT_LABELS"),
        output_data=_env("OUTPUT_DATA"),
        output_labels=_env("OUTPUT_LABELS"),
        metadata=_env("METADATA"),
        parameters_file=_env("PARAMETERS_FILE"),
        additional_files=_env("ADDITIONAL_FILES"),
        report_file=_env("REPORT_FILE"),
        statistics_file=_env("STATISTICS_FILE"),
        work_dir=os.path.join(_env("OUTPUT_DATA"), ".work"),
    )


def load_registries(
    project_dir: str,
) -> Tuple[Dict[str, Step], Dict[str, Condition]]:
    """Discover author Step/Condition classes and instantiate them (with builtins)."""
    add_to_path(project_dir)
    step_classes = dict(builtin_steps())
    step_classes.update(discover_steps())
    condition_classes = discover_conditions()
    steps = {name: cls() for name, cls in step_classes.items()}
    conditions = {name: cls() for name, cls in condition_classes.items()}
    return steps, conditions


def build_engine(workflow_yaml: str, project_dir: str, paths: Paths) -> Engine:
    graph = Graph.from_yaml(workflow_yaml)
    steps, conditions = load_registries(project_dir)
    _check_registered(graph, steps, conditions)
    report = Report(paths.report_file)
    factory = ContextFactory(paths, report)
    return Engine(graph, steps, conditions, factory)


def _check_registered(graph: Graph, steps: Dict, conditions: Dict) -> None:
    missing_steps = sorted(set(graph.step_names()) - set(steps))
    if missing_steps:
        raise SystemExit(f"workflow.yaml references unknown steps: {missing_steps}")
    missing_conditions = sorted(set(graph.condition_names()) - set(conditions))
    if missing_conditions:
        raise SystemExit(
            f"workflow.yaml references unknown conditions: {missing_conditions}"
        )

    try:
        graph.start_at(SANITY_CHECK_START)
    except WorkflowError as exc:
        raise SystemExit(str(exc)) from exc

    required_steps = (SANITY_CHECK_STEP, STATISTICS_STEP)
    prepare_steps = graph.reachable_step_names(PREPARE_START)
    overlapping_steps = [name for name in required_steps if name in prepare_steps]
    if overlapping_steps:
        raise SystemExit(
            "workflow.yaml prepare flow must stop before validation; "
            f"unexpected steps: {overlapping_steps}"
        )

    validation_steps = graph.reachable_step_names(SANITY_CHECK_START)
    missing_required = [name for name in required_steps if name not in validation_steps]
    if missing_required:
        raise SystemExit(
            f"workflow.yaml step '{SANITY_CHECK_START}' must reach "
            f"{list(required_steps)}; missing: {missing_required}"
        )


def main(argv=None) -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    parser = argparse.ArgumentParser(description="MedPerf data-prep workflow runner")
    parser.add_argument("--start", choices=list(STARTS), default=PREPARE_START)
    args = parser.parse_args(argv)

    engine = build_engine(_env("WORKFLOW_YAML"), _env("PROJECT_DIR"), build_paths())
    engine.run(args.start, resume=args.start == PREPARE_START)


if __name__ == "__main__":
    sys.exit(main())
