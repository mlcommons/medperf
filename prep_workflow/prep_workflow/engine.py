"""The workflow engine: a parallel, per-subject scheduler over the node graph.

Each subject flows through the graph independently (so one subject can sit in a
human-review step while another keeps computing), bounded by a global worker pool
and per-step concurrency limits. Barrier steps (``per_subject: false``) run once,
after every live subject has reached them. Branch decisions, cycles, wait/retry
loops, per-subject error handling, and resume-from-report are all handled here.

All graph-state bookkeeping happens on the single coordinator thread (the one
that calls ``run``); worker threads only execute a step and drop a message on a
queue, so the coordinator needs no locks around its own structures.
"""

from __future__ import annotations

import heapq
import logging
import queue
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Set

from prep_workflow.context import ContextFactory
from prep_workflow.graph import (
    PREPARE_START,
    SANITY_CHECK_START,
    Branch,
    Graph,
    Node,
)


class EngineError(Exception):
    pass


class Engine:
    def __init__(
        self,
        graph: Graph,
        steps: Dict[str, object],
        conditions: Dict[str, object],
        context_factory: ContextFactory,
        logger: Optional[logging.Logger] = None,
        time_fn=time.monotonic,
    ):
        self.graph = graph
        self.steps = steps
        self.conditions = conditions
        self.cf = context_factory
        self.report = context_factory.report
        self.log = logger or logging.getLogger("prep")
        self._now = time_fn

        self._results: "queue.Queue" = queue.Queue()
        self._ready: List = []  # (subject, node_id) runnable now
        self._scheduled: List = []  # heap of (due, subject, node_id) branch re-checks
        self._barrier_arrived: Dict[str, Set[str]] = {}
        self._barrier_running: Set[str] = set()
        self._barrier_fired: Dict[str, Set[str]] = {}
        self._semaphores = {
            n.id: threading.Semaphore(n.limit) for n in graph.nodes.values() if n.limit
        }
        self._inflight = 0
        self._live: Set[str] = set()
        self._all_subjects: List[str] = []
        self._failed: Optional[BaseException] = None
        self._start: Optional[Node] = None
        self._entrypoint = PREPARE_START
        self._touch_report = True

    # ---- public ----------------------------------------------------------------
    def run(self, entrypoint: str = PREPARE_START, resume: bool = True) -> None:
        self._entrypoint = entrypoint
        self._start = self.graph.start_at(entrypoint)
        self._touch_report = resume
        self.report.load()
        with ThreadPoolExecutor(max_workers=self.graph.max_workers) as self._pool:
            self._seed(resume)
            self._loop()
        if self._failed is not None:
            raise self._failed

    # ---- seeding / resume ------------------------------------------------------
    def _seed(self, resume: bool) -> None:
        start = self._start
        if not resume:
            # Validation runs over already-prepared data and must not alter the
            # preparation resume state. A synthetic subject drives dataset-wide
            # barriers when no preparation report exists (submit-as-prepared).
            self._all_subjects = self.report.subjects() or ["dataset"]
            self._live = set(self._all_subjects)
            for subject in self._all_subjects:
                self._arrive(subject, start.id)
            return

        fresh = not self.report.has_subjects()
        if fresh:
            ctx = self.cf.make(None, [], start.config)
            self.steps[start.step_name].run(ctx)  # registers subjects in the report

        self._all_subjects = self.report.subjects()
        if not self._all_subjects:
            raise EngineError(
                f"start step '{start.id}' registered no subjects; nothing to prepare"
            )
        self._live = {s for s in self._all_subjects if not self.report.is_done(s)}

        if fresh:
            for subject in self._all_subjects:
                self.report.set_status(subject, start.ordinal, start.id)
                self._advance(subject, start)
        else:
            for subject in list(self._live):
                self._resume(subject)

    def _resume(self, subject: str) -> None:
        node_id = self.report.get_node(subject)
        if node_id not in self.graph.nodes:
            # crashed before the first transition was recorded; restart after start
            self._advance(subject, self._start)
        else:
            self._arrive(subject, node_id)

    # ---- coordinator loop ------------------------------------------------------
    def _loop(self) -> None:
        while self._live and self._failed is None:
            self._pump_ready()
            self._pump_barriers()
            timeout = self._next_delay()
            if self._inflight == 0 and not self._ready and timeout is None:
                raise EngineError(
                    "workflow stalled: live subjects remain but no work is runnable"
                )
            try:
                msg = self._results.get(timeout=timeout)
            except queue.Empty:
                self._process_due_decisions()
                continue
            self._handle_result(msg)

    def _pump_ready(self) -> None:
        held = []
        for subject, node_id in self._ready:
            sem = self._semaphores.get(node_id)
            if sem is not None and not sem.acquire(blocking=False):
                held.append((subject, node_id))
                continue
            self._submit(self.graph.node(node_id), subject)
        self._ready = held

    def _pump_barriers(self) -> None:
        for node_id, arrived in self._barrier_arrived.items():
            if not arrived or node_id in self._barrier_running:
                continue
            if arrived == self._live:
                self._barrier_running.add(node_id)
                self._barrier_fired[node_id] = set(arrived)
                arrived.clear()
                self._submit(self.graph.node(node_id), None)

    def _submit(self, node: Node, subject: Optional[str]) -> None:
        self._inflight += 1
        self._pool.submit(self._task, node, subject)

    def _task(self, node: Node, subject: Optional[str]) -> None:
        try:
            ctx = self.cf.make(subject, self._all_subjects, node.config)
            self.steps[node.step_name].run(ctx)
            self._results.put(("done", node.id, subject))
        except BaseException as exc:  # noqa: BLE001 - reported back to the coordinator
            self._results.put(("error", node.id, subject, exc, traceback.format_exc()))

    # ---- result handling -------------------------------------------------------
    def _handle_result(self, msg) -> None:
        kind = msg[0]
        node = self.graph.node(msg[1])
        self._release(node.id)
        self._inflight -= 1

        if kind == "error":
            _, _, subject, exc, tb = msg
            self._handle_error(node, subject, exc, tb)
            return

        subject = msg[2]
        if node.per_subject:
            if self._touch_report:
                self.report.set_status(subject, node.ordinal, node.id)
            self._advance(subject, node)
        else:
            self._barrier_running.discard(node.id)
            for s in self._barrier_fired.pop(node.id, set()):
                if s not in self._live:
                    continue
                if self._touch_report:
                    self.report.set_status(s, node.ordinal, node.id)
                self._advance(s, node)

    def _handle_error(self, node: Node, subject, exc, tb: str) -> None:
        if subject is None:  # a barrier failing is dataset-wide -> fatal
            self._barrier_running.discard(node.id)
            self.log.error("Barrier step '%s' failed:\n%s", node.id, tb)
            self._failed = exc
            return
        if self._touch_report:
            self.report.set_error(subject, node.ordinal, node.id, tb)
        if node.on_error == "ignore":
            self.log.warning("Subject '%s' failed at '%s'; skipping.", subject, node.id)
            self._invalidate(subject)
        else:
            self.log.error("Subject '%s' failed at '%s':\n%s", subject, node.id, tb)
            self._failed = exc

    # ---- transitions -----------------------------------------------------------
    def _advance(self, subject: str, node: Node) -> None:
        nxt = node.nxt
        if nxt is None:
            if self._touch_report:
                self.report.mark_done(subject)
            self._live.discard(subject)
        elif isinstance(nxt, str):
            self._arrive(subject, nxt)
        else:
            self._decide(subject, node)

    def _arrive(self, subject: str, target_id: str) -> None:
        # Preparation keep next: sanity_check in YAML for readability, but
        # the prepare run must stop at that boundary.
        if self._entrypoint == PREPARE_START and target_id == SANITY_CHECK_START:
            if self._touch_report:
                self.report.mark_done(subject)
            self._live.discard(subject)
            return

        target = self.graph.node(target_id)
        if self._touch_report:
            self.report.set_node(subject, target_id)
        if target.per_subject:
            self._ready.append((subject, target_id))
        else:
            self._barrier_arrived.setdefault(target_id, set()).add(subject)

    def _decide(self, subject: str, node: Node) -> None:
        branch: Branch = node.nxt
        ctx = self.cf.make(subject, self._all_subjects, node.config)
        for cond_name, target in branch.conditions:
            if self.conditions[cond_name].evaluate(ctx):
                self._arrive(subject, target)
                return
        if branch.else_target and branch.else_target != node.id:
            self._arrive(subject, branch.else_target)
            return
        # loop back to self: wait, then re-evaluate (the step is NOT re-run)
        if self._touch_report:
            self.report.set_node(subject, node.id)
        heapq.heappush(self._scheduled, (self._now() + branch.wait, subject, node.id))

    def _process_due_decisions(self) -> None:
        now = self._now()
        while self._scheduled and self._scheduled[0][0] <= now:
            _, subject, node_id = heapq.heappop(self._scheduled)
            if subject in self._live:
                self._decide(subject, self.graph.node(node_id))

    # ---- helpers ---------------------------------------------------------------
    def _invalidate(self, subject: str) -> None:
        self._live.discard(subject)
        for arrived in self._barrier_arrived.values():
            arrived.discard(subject)

    def _release(self, node_id: str) -> None:
        sem = self._semaphores.get(node_id)
        if sem is not None:
            sem.release()

    def _next_delay(self) -> Optional[float]:
        if not self._scheduled:
            return None
        return max(0.0, self._scheduled[0][0] - self._now())
