"""Parse and validate ``workflow.yaml`` into an executable node graph.

Only the *control* graph lives in YAML (which step follows which, and under what
condition). Data flow is implicit: every step shares the container filesystem, so
there are no per-step images or mounts.

Starts are conventional rather than declared: preparation begins at the first
step, and ``--start=sanity_check`` begins at the step whose ``id`` is
``sanity_check``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union

import yaml

DEFAULT_WAIT = 60.0
MANUAL_APPROVAL = "manual_approval"
MANUAL_APPROVAL_STEP = "ManualApproval"
PREPARE_START = "prepare"
SANITY_CHECK_START = "sanity_check"


class WorkflowError(Exception):
    """Raised for malformed ``workflow.yaml`` files."""


@dataclass
class Branch:
    """A conditional ``next``: try each condition in order; fall back to ``else``."""

    conditions: List[Tuple[str, str]]  # (condition_name, target_id), evaluated in order
    else_target: Optional[str]
    wait: float = DEFAULT_WAIT


NextSpec = Union[None, str, Branch]  # terminal | linear target | branch


@dataclass
class Node:
    id: str
    kind: str  # "step" | "manual_approval"
    step_name: Optional[str]
    per_subject: bool
    nxt: NextSpec
    ordinal: int
    limit: Optional[int] = None
    on_error: str = "stop"
    config: Dict = field(default_factory=dict)

    @property
    def is_terminal(self) -> bool:
        return self.nxt is None


class Graph:
    def __init__(self, nodes: Dict[str, Node], start_id: str, max_workers: int):
        self.nodes = nodes
        self.start_id = start_id
        self.max_workers = max_workers

    def node(self, node_id: str) -> Node:
        return self.nodes[node_id]

    def start_at(self, name: str = PREPARE_START) -> Node:
        """Resolve a start name to a node.

        ``prepare`` always begins at the first workflow step. Any other name is
        treated as a step id (e.g. ``sanity_check``).
        """
        if name == PREPARE_START:
            return self.start
        if name not in self.nodes:
            raise WorkflowError(f"workflow.yaml has no step with id '{name}'")
        return self.nodes[name]

    @property
    def start(self) -> Node:
        return self.nodes[self.start_id]

    def step_names(self) -> List[str]:
        return [n.step_name for n in self.nodes.values() if n.step_name]

    def condition_names(self) -> List[str]:
        names = []
        for n in self.nodes.values():
            if isinstance(n.nxt, Branch):
                names.extend(c for c, _ in n.nxt.conditions)
        return names

    def reachable_step_names(self, start_name: str = PREPARE_START) -> List[str]:
        """Return step names reachable from a conventional start.

        Preparation keep ``next: sanity_check of the last prepare step`` so the YAML reads as one
        continuous graph, but prepare reachability stops *before*
        ``sanity_check`` - that boundary is only crossed by
        ``--start=sanity_check``.
        """
        pending = [self.start_at(start_name).id]
        visited = set()
        names = []
        stop_before = SANITY_CHECK_START if start_name == PREPARE_START else None
        while pending:
            node_id = pending.pop()
            if node_id in visited:
                continue
            if stop_before and node_id == stop_before:
                continue
            visited.add(node_id)
            node = self.node(node_id)
            if node.step_name:
                names.append(node.step_name)
            pending.extend(_targets(node))
        return names

    # ---- construction ----------------------------------------------------------
    @classmethod
    def from_yaml(cls, path: str) -> "Graph":
        with open(path) as f:
            spec = yaml.safe_load(f) or {}
        return cls.from_spec(spec)

    @classmethod
    def from_spec(cls, spec: dict) -> "Graph":
        raw_steps = spec.get("steps")
        if not raw_steps:
            raise WorkflowError("workflow.yaml must define a non-empty 'steps' list")

        max_workers = int(spec.get("max_workers", 4))
        nodes: Dict[str, Node] = {}
        for ordinal, raw in enumerate(raw_steps, start=1):
            node = _parse_node(raw, ordinal)
            if node.id in nodes:
                raise WorkflowError(f"duplicate step id: {node.id}")
            nodes[node.id] = node

        start_id = raw_steps[0]["id"]
        graph = cls(nodes, start_id, max_workers)
        _validate(graph)
        return graph


def _parse_node(raw: dict, ordinal: int) -> Node:
    if "id" not in raw:
        raise WorkflowError(f"step #{ordinal} is missing an 'id'")
    node_id = raw["id"]
    kind = raw.get("type", "step")
    if kind not in ("step", MANUAL_APPROVAL):
        raise WorkflowError(f"step '{node_id}' has unknown type '{kind}'")

    if kind == MANUAL_APPROVAL:
        step_name = MANUAL_APPROVAL_STEP
        per_subject = raw.get("per_subject", False)
    else:
        step_name = raw.get("step", node_id)
        per_subject = raw.get("per_subject", True)

    return Node(
        id=node_id,
        kind=kind,
        step_name=step_name,
        per_subject=per_subject,
        nxt=_parse_next(raw.get("next"), node_id),
        ordinal=ordinal,
        limit=raw.get("limit"),
        on_error=raw.get("on_error", "stop"),
        config=raw.get("config", {}) or {},
    )


def _parse_next(raw_next, node_id: str) -> NextSpec:
    if raw_next is None:
        return None
    if isinstance(raw_next, str):
        return raw_next
    if isinstance(raw_next, dict):
        conditions = []
        for entry in raw_next.get("if", []):
            conditions.append((entry["condition"], entry["target"]))
        return Branch(
            conditions=conditions,
            else_target=raw_next.get("else"),
            wait=float(raw_next.get("wait", DEFAULT_WAIT)),
        )
    raise WorkflowError(f"step '{node_id}' has an invalid 'next': {raw_next!r}")


def _targets(node: Node) -> List[str]:
    if node.nxt is None:
        return []
    if isinstance(node.nxt, str):
        return [node.nxt]
    targets = [t for _, t in node.nxt.conditions]
    if node.nxt.else_target:
        targets.append(node.nxt.else_target)
    return targets


def _validate(graph: Graph) -> None:
    ids = set(graph.nodes)

    for node in graph.nodes.values():
        for target in _targets(node):
            if target not in ids:
                raise WorkflowError(
                    f"step '{node.id}' points to unknown step '{target}'"
                )
        if node.on_error not in ("stop", "ignore"):
            raise WorkflowError(
                f"step '{node.id}' has invalid on_error '{node.on_error}' "
                "(expected 'stop' or 'ignore')"
            )

    if not any(n.is_terminal for n in graph.nodes.values()):
        raise WorkflowError(
            "at least one terminal step (next: null) is required so the workflow can complete"
        )

    if graph.start.per_subject:
        raise WorkflowError(
            f"the first step '{graph.start_id}' must be a barrier (per_subject: false) "
            "so it can establish the subject list"
        )

    if SANITY_CHECK_START in graph.nodes and graph.node(SANITY_CHECK_START).per_subject:
        raise WorkflowError(
            f"step '{SANITY_CHECK_START}' must be a barrier (per_subject: false)"
        )

    # The preparation graph should stay visually continuous (last prep step
    # points at sanity_check) while the prepare run still stops at that boundary.
    if SANITY_CHECK_START in graph.nodes:
        predecessors = [
            n.id for n in graph.nodes.values() if SANITY_CHECK_START in _targets(n)
        ]
        if not predecessors:
            raise WorkflowError(
                f"the last preparation step must set next: {SANITY_CHECK_START} "
                "(prepare still stops before that step at runtime)"
            )
