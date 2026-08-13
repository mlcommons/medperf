"""Build the per-execution ``Context`` handed to steps and conditions."""

from __future__ import annotations

import logging
import os
from typing import Dict, List, Optional

import yaml

from prep_workflow.base import Context, Paths
from prep_workflow.report import Report


def load_params(parameters_file: str) -> Dict:
    if parameters_file and os.path.exists(parameters_file):
        with open(parameters_file) as f:
            return yaml.safe_load(f) or {}
    return {}


class ContextFactory:
    """Creates a fresh ``Context`` for each step/condition invocation.

    A single factory is built once per run holding the immutable bits (paths,
    params, report, subject list); ``make`` stamps in the per-call subject and
    node config.
    """

    def __init__(
        self,
        paths: Paths,
        report: Report,
        params: Optional[Dict] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.paths = paths
        self.report = report
        self.params = params if params is not None else load_params(paths.parameters_file)
        self.logger = logger or logging.getLogger("prep")

    def make(
        self,
        subject: Optional[str],
        subjects: List[str],
        config: Optional[Dict] = None,
    ) -> Context:
        return Context(
            subject=subject,
            subjects=subjects,
            paths=self.paths,
            params=self.params,
            config=config or {},
            report=self.report,
            logger=self.logger,
        )
