import pytest

from prep_workflow.graph import Branch, Graph, WorkflowError


def _linear_spec():
    return {
        "steps": [
            {"id": "setup", "per_subject": False, "next": "a"},
            {"id": "a", "next": "b"},
            {"id": "b", "next": None},
        ]
    }


def test_parses_linear_chain():
    graph = Graph.from_spec(_linear_spec())
    assert graph.start_id == "setup"
    assert graph.node("a").nxt == "b"
    assert graph.node("b").is_terminal
    assert graph.node("a").ordinal == 2


def test_start_at_prepare_uses_first_step():
    graph = Graph.from_spec(_linear_spec())
    assert graph.start_at("prepare").id == "setup"
    assert graph.start_at().id == "setup"


def test_start_at_resolves_step_id():
    spec = {
        "steps": [
            {"id": "setup", "per_subject": False, "next": "sanity_check"},
            {"id": "sanity_check", "per_subject": False, "next": None},
        ]
    }
    graph = Graph.from_spec(spec)
    assert graph.start_at("sanity_check").id == "sanity_check"
    assert graph.reachable_step_names("sanity_check") == ["sanity_check"]
    # prepare reachability stops before sanity_check even when next points there
    assert "sanity_check" not in graph.reachable_step_names("prepare")


def test_start_at_unknown_step_id():
    graph = Graph.from_spec(_linear_spec())
    with pytest.raises(WorkflowError, match="no step with id"):
        graph.start_at("missing")


def test_sanity_check_step_must_be_barrier():
    spec = {
        "steps": [
            {"id": "setup", "per_subject": False, "next": "sanity_check"},
            {"id": "sanity_check", "per_subject": True, "next": None},
        ]
    }
    with pytest.raises(WorkflowError, match="barrier"):
        Graph.from_spec(spec)


def test_preparation_must_connect_into_sanity_check():
    spec = {
        "steps": [
            {"id": "setup", "per_subject": False, "next": None},
            {"id": "sanity_check", "per_subject": False, "next": None},
        ]
    }
    with pytest.raises(WorkflowError, match="next: sanity_check"):
        Graph.from_spec(spec)


def test_parses_branch():
    spec = {
        "steps": [
            {"id": "setup", "per_subject": False, "next": "review"},
            {
                "id": "review",
                "next": {
                    "if": [
                        {"condition": "Done", "target": "finish"},
                        {"condition": "Redo", "target": "review"},
                    ],
                    "else": "review",
                    "wait": 5,
                },
            },
            {"id": "finish", "next": None},
        ]
    }
    branch = Graph.from_spec(spec).node("review").nxt
    assert isinstance(branch, Branch)
    assert branch.conditions == [("Done", "finish"), ("Redo", "review")]
    assert branch.else_target == "review"
    assert branch.wait == 5


def test_manual_approval_is_a_barrier():
    spec = {
        "steps": [
            {"id": "setup", "per_subject": False, "next": "gate"},
            {"id": "gate", "type": "manual_approval", "next": None},
        ]
    }
    node = Graph.from_spec(spec).node("gate")
    assert node.per_subject is False
    assert node.step_name == "ManualApproval"


def test_rejects_unknown_target():
    spec = {"steps": [{"id": "setup", "per_subject": False, "next": "nope"}]}
    with pytest.raises(WorkflowError, match="unknown step"):
        Graph.from_spec(spec)


def test_requires_exactly_one_terminal():
    spec = {
        "steps": [
            {"id": "setup", "per_subject": False, "next": "a"},
            {"id": "a", "next": "setup"},  # no terminal -> cycle only
        ]
    }
    with pytest.raises(WorkflowError, match="terminal"):
        Graph.from_spec(spec)


def test_start_must_be_barrier():
    spec = {"steps": [{"id": "setup", "per_subject": True, "next": None}]}
    with pytest.raises(WorkflowError, match="barrier"):
        Graph.from_spec(spec)


def test_rejects_duplicate_ids():
    spec = {
        "steps": [
            {"id": "setup", "per_subject": False, "next": "a"},
            {"id": "a", "next": None},
            {"id": "a", "next": None},
        ]
    }
    with pytest.raises(WorkflowError, match="duplicate"):
        Graph.from_spec(spec)
