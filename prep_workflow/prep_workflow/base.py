"""Core interfaces a workflow author implements.

A data-preparation pipeline is expressed as a set of ``Step`` classes (the units
of work) and ``Condition`` classes (boolean predicates used for branching). Both
are discovered automatically by name and driven by ``workflow.yaml``. Everything
a step or condition needs at runtime is handed to it through a single ``Context``
object, so the classes stay small and their constructors stay empty.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:  # avoid a runtime import cycle (report imports nothing from here)
    from prep_workflow.report import Report


@dataclass
class Paths:
    """Filesystem locations available to every step, taken from the standard
    MedPerf data-preparation mount points."""

    input_data: str
    input_labels: str
    output_data: str
    output_labels: str
    metadata: str
    parameters_file: str
    additional_files: str
    report_file: str
    statistics_file: str
    work_dir: str


@dataclass
class Context:
    """Everything a step or condition needs to run.

    ``subject`` is the case currently being processed for per-subject steps and
    conditions; it is ``None`` for barrier (whole-dataset) steps, where the full
    list is available through ``subjects``.
    """

    subject: Optional[str]
    subjects: List[str]
    paths: Paths
    params: Dict = field(default_factory=dict)
    config: Dict = field(default_factory=dict)  # per-step 'config' block from workflow.yaml
    report: "Report" = None
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger("prep"))


class Step(ABC):
    """A unit of work in the pipeline.

    Set ``per_subject = False`` for a barrier step that runs once over the whole
    dataset (after every subject has reached it). ``name`` defaults to the class
    name and is how the step is referenced from ``workflow.yaml``.
    """

    name: Optional[str] = None
    per_subject: bool = True

    @abstractmethod
    def run(self, ctx: Context) -> None:
        """Perform the work. Raise an exception to signal failure."""


class Condition(ABC):
    """A boolean predicate the engine evaluates to choose a branch."""

    name: Optional[str] = None

    @abstractmethod
    def evaluate(self, ctx: Context) -> bool:
        """Return ``True`` when the branch this condition guards should be taken."""


def registered_name(cls: type) -> str:
    """The name a Step/Condition subclass is registered and referenced under."""
    return cls.name or cls.__name__
