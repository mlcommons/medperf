"""Guard the shipped example workflow graphs against drift."""

import os

from prep_workflow.graph import Branch, Graph

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_template_workflow_is_valid():
    graph = Graph.from_yaml(os.path.join(ROOT, "template/project/workflow.yaml"))
    assert graph.start_id == "discover"
    # YAML is continuous (collect -> sanity_check), but prepare stops before sanity_check.
    assert graph.node("collect").nxt == "sanity_check"
    assert graph.node("statistics").is_terminal
    assert "SanityCheck" not in graph.reachable_step_names("prepare")
    assert "Statistics" in graph.reachable_step_names("sanity_check")


def test_ported_example_workflows_are_valid():
    for rel in [
        "examples/chestxray/project/workflow.yaml",
        "examples/hemnet/project/workflow.yaml",
        "examples/rano/project/workflow.yaml",
    ]:
        graph = Graph.from_yaml(os.path.join(ROOT, rel))
        assert graph.node("sanity_check").id in {
            t
            for n in graph.nodes.values()
            for t in ([n.nxt] if isinstance(n.nxt, str) else [])
        }
        assert "SanityCheck" not in graph.reachable_step_names("prepare")
        assert "Statistics" not in graph.reachable_step_names("prepare")
        assert graph.start_at("sanity_check").step_name == "SanityCheck"
        assert "Statistics" in graph.reachable_step_names("sanity_check")


def test_rano_workflow_has_expected_shape():
    graph = Graph.from_yaml(os.path.join(ROOT, "examples/rano/project/workflow.yaml"))
    # branch with two conditions + wait/else loop
    review = graph.node("manual_review").nxt
    assert isinstance(review, Branch)
    assert [c for c, _ in review.conditions] == ["AnnotationDone", "BrainMaskChanged"]
    assert review.else_target == "manual_review"
    # rollback cycles back to an earlier step
    assert graph.node("rollback").nxt == "brain_extraction"
    # barrier join + manual-approval gate + continuous flow into validation
    assert graph.node("calculate_changed_voxels").per_subject is False
    assert graph.node("final_confirmation").step_name == "ManualApproval"
    assert graph.node("consolidate").nxt == "sanity_check"
    assert graph.node("statistics").is_terminal
