"""Shared test doubles and an engine builder for the unit tests."""

from __future__ import annotations

import threading
import time

from prep_workflow.base import Condition, Paths, Step
from prep_workflow.context import ContextFactory
from prep_workflow.engine import Engine
from prep_workflow.graph import Graph
from prep_workflow.report import Report


class Recorder:
    """Thread-safe log of step start/end events, tracking peak concurrency."""

    def __init__(self):
        self._lock = threading.Lock()
        self.events = []          # (phase, node, subject)
        self.active = {}          # node -> current concurrency
        self.peak = {}            # node -> peak concurrency

    def enter(self, node, subject):
        with self._lock:
            self.events.append(("start", node, subject))
            self.active[node] = self.active.get(node, 0) + 1
            self.peak[node] = max(self.peak.get(node, 0), self.active[node])

    def leave(self, node, subject):
        with self._lock:
            self.events.append(("end", node, subject))
            self.active[node] -= 1

    def runs(self, node):
        return [s for phase, n, s in self.events if n == node and phase == "start"]

    def order(self):
        return [(phase, n, s) for phase, n, s in self.events]


class SeedStep(Step):
    """Barrier first step that registers a fixed subject list."""

    per_subject = False

    def __init__(self, subjects, node_name="seed"):
        self._subjects = subjects
        self.name = node_name

    def run(self, ctx):
        for subject in self._subjects:
            ctx.report.add_subject(subject)


class RecordStep(Step):
    """Records its execution; optionally sleeps and/or fails for given subjects."""

    def __init__(self, node_name, recorder, sleep=0.0, fail_for=(), per_subject=True):
        self.name = node_name
        self.per_subject = per_subject
        self._rec = recorder
        self._sleep = sleep
        self._fail_for = set(fail_for)

    def run(self, ctx):
        self._rec.enter(self.name, ctx.subject)
        try:
            if self._sleep:
                time.sleep(self._sleep)
            if ctx.subject in self._fail_for:
                raise RuntimeError(f"boom on {ctx.subject}")
        finally:
            self._rec.leave(self.name, ctx.subject)


class CountingCondition(Condition):
    """True only after it has been evaluated ``true_after`` times (per subject)."""

    def __init__(self, name, true_after=1):
        self.name = name
        self._true_after = true_after
        self._counts = {}

    def evaluate(self, ctx):
        self._counts[ctx.subject] = self._counts.get(ctx.subject, 0) + 1
        return self._counts[ctx.subject] >= self._true_after


class OnceCondition(Condition):
    """True on its first evaluation per subject, False afterwards."""

    def __init__(self, name):
        self.name = name
        self._seen = set()

    def evaluate(self, ctx):
        first = ctx.subject not in self._seen
        self._seen.add(ctx.subject)
        return first


def make_paths(tmp_path):
    return Paths(
        input_data=str(tmp_path / "in"),
        input_labels=str(tmp_path / "in_labels"),
        output_data=str(tmp_path / "out"),
        output_labels=str(tmp_path / "out_labels"),
        metadata=str(tmp_path / "metadata"),
        parameters_file=str(tmp_path / "params.yaml"),
        additional_files=str(tmp_path / "additional"),
        report_file=str(tmp_path / "report.yaml"),
        statistics_file=str(tmp_path / "statistics.yaml"),
        work_dir=str(tmp_path / "work"),
    )


def build_engine(tmp_path, spec, steps, conditions=None):
    graph = Graph.from_spec(spec)
    paths = make_paths(tmp_path)
    report = Report(paths.report_file)
    factory = ContextFactory(paths, report, params={})
    engine = Engine(graph, steps, conditions or {}, factory)
    return engine, report
