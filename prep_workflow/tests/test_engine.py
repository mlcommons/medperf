import time

import pytest
import yaml

from prep_workflow.report import Report

from ._helpers import (
    CountingCondition,
    OnceCondition,
    RecordStep,
    SeedStep,
    build_engine,
    make_paths,
)


def test_linear_pipeline_runs_all_subjects(tmp_path):
    from ._helpers import Recorder

    recorder = Recorder()
    steps = {
        "seed": SeedStep(["s1", "s2", "s3"]),
        "a": RecordStep("a", recorder),
        "b": RecordStep("b", recorder),
        "c": RecordStep("c", recorder),
    }
    spec = {
        "steps": [
            {"id": "seed", "per_subject": False, "next": "a"},
            {"id": "a", "next": "b"},
            {"id": "b", "next": "c"},
            {"id": "c", "next": None},
        ]
    }
    engine, report = build_engine(tmp_path, spec, steps)
    engine.run()

    for subject in ["s1", "s2", "s3"]:
        assert report.is_done(subject)
    assert sorted(recorder.runs("a")) == ["s1", "s2", "s3"]
    assert sorted(recorder.runs("c")) == ["s1", "s2", "s3"]


def test_subjects_run_in_parallel(tmp_path):
    from ._helpers import Recorder

    recorder = Recorder()
    steps = {
        "seed": SeedStep(["s1", "s2", "s3"]),
        "work": RecordStep("work", recorder, sleep=0.2),
    }
    spec = {
        "steps": [
            {"id": "seed", "per_subject": False, "next": "work"},
            {"id": "work", "next": None},
        ],
        "max_workers": 3,
    }
    engine, _ = build_engine(tmp_path, spec, steps)
    start = time.monotonic()
    engine.run()
    elapsed = time.monotonic() - start

    assert recorder.peak["work"] == 3  # all three ran concurrently
    assert elapsed < 0.5  # would be ~0.6s if serialized


def test_limit_caps_concurrency(tmp_path):
    from ._helpers import Recorder

    recorder = Recorder()
    steps = {
        "seed": SeedStep(["s1", "s2", "s3", "s4"]),
        "work": RecordStep("work", recorder, sleep=0.1),
    }
    spec = {
        "steps": [
            {"id": "seed", "per_subject": False, "next": "work"},
            {"id": "work", "limit": 2, "next": None},
        ],
        "max_workers": 8,
    }
    engine, _ = build_engine(tmp_path, spec, steps)
    engine.run()
    assert recorder.peak["work"] == 2  # never more than the limit


def test_pipelining_a_slow_subject_does_not_block_others(tmp_path):
    from ._helpers import Recorder

    recorder = Recorder()
    # the slow subject spends a long time in step1 while the others should sail
    # through step1 -> step2 -> done without waiting for it
    steps = {
        "seed": SeedStep(["fast1", "fast2", "slow"]),
        "step1": _SubjectAwareSleep("step1", recorder, {"slow": 0.3}),
        "step2": RecordStep("step2", recorder),
    }
    spec = {
        "steps": [
            {"id": "seed", "per_subject": False, "next": "step1"},
            {"id": "step1", "next": "step2"},
            {"id": "step2", "next": None},
        ],
        "max_workers": 3,
    }
    engine, report = build_engine(tmp_path, spec, steps)
    engine.run()
    order = recorder.order()
    # fast subjects finished step2 before the slow subject finished step1
    slow_step1_end = order.index(("end", "step1", "slow"))
    fast_step2_starts = [
        i
        for i, (p, n, s) in enumerate(order)
        if p == "start" and n == "step2" and s in ("fast1", "fast2")
    ]
    assert any(i < slow_step1_end for i in fast_step2_starts)


class _SubjectAwareSleep(RecordStep):
    def __init__(self, node_name, recorder, sleeps):
        super().__init__(node_name, recorder)
        self._sleeps = sleeps

    def run(self, ctx):
        self._rec.enter(self.name, ctx.subject)
        try:
            time.sleep(self._sleeps.get(ctx.subject, 0.0))
        finally:
            self._rec.leave(self.name, ctx.subject)


def test_branch_selects_condition_target(tmp_path):
    from ._helpers import Recorder

    recorder = Recorder()
    steps = {
        "seed": SeedStep(["s1"]),
        "review": RecordStep("review", recorder),
        "good": RecordStep("good", recorder),
        "bad": RecordStep("bad", recorder),
    }
    conditions = {"IsGood": CountingCondition("IsGood", true_after=1)}
    spec = {
        "steps": [
            {"id": "seed", "per_subject": False, "next": "review"},
            {
                "id": "review",
                "next": {
                    "if": [{"condition": "IsGood", "target": "good"}],
                    "else": "bad",
                },
            },
            {"id": "good", "next": None},
            {"id": "bad", "next": None},
        ]
    }
    engine, _ = build_engine(tmp_path, spec, steps, conditions)
    engine.run()
    assert recorder.runs("good") == ["s1"]
    assert recorder.runs("bad") == []


def test_branch_waits_then_proceeds(tmp_path):
    from ._helpers import Recorder

    recorder = Recorder()
    steps = {
        "seed": SeedStep(["s1"]),
        "review": RecordStep("review", recorder),
        "done": RecordStep("done", recorder),
    }
    # condition true only on the 3rd poll -> forces the else:self wait loop twice
    conditions = {"Ready": CountingCondition("Ready", true_after=3)}
    spec = {
        "steps": [
            {"id": "seed", "per_subject": False, "next": "review"},
            {
                "id": "review",
                "next": {
                    "if": [{"condition": "Ready", "target": "done"}],
                    "else": "review",
                    "wait": 0.05,
                },
            },
            {"id": "done", "next": None},
        ]
    }
    engine, _ = build_engine(tmp_path, spec, steps, conditions)
    engine.run()
    # review step ran exactly once (the wait loop re-checks the condition, not the step)
    assert recorder.runs("review") == ["s1"]
    assert recorder.runs("done") == ["s1"]


def test_cycle_reruns_step(tmp_path):
    from ._helpers import Recorder

    recorder = Recorder()
    steps = {
        "seed": SeedStep(["s1"]),
        "a": RecordStep("a", recorder),
        "review": RecordStep("review", recorder),
        "done": RecordStep("done", recorder),
    }
    conditions = {"Redo": OnceCondition("Redo")}
    spec = {
        "steps": [
            {"id": "seed", "per_subject": False, "next": "a"},
            {"id": "a", "next": "review"},
            {
                "id": "review",
                "next": {
                    "if": [{"condition": "Redo", "target": "a"}],
                    "else": "done",
                },
            },
            {"id": "done", "next": None},
        ]
    }
    engine, _ = build_engine(tmp_path, spec, steps, conditions)
    engine.run()
    assert recorder.runs("a") == ["s1", "s1"]  # ran twice due to the cycle
    assert recorder.runs("done") == ["s1"]


def test_barrier_runs_once_after_all_subjects(tmp_path):
    from ._helpers import Recorder

    recorder = Recorder()
    steps = {
        "seed": SeedStep(["s1", "s2", "s3"]),
        "per": _SubjectAwareSleep(
            "per", recorder, {"s1": 0.05, "s2": 0.15, "s3": 0.25}
        ),
        "barrier": RecordStep("barrier", recorder, per_subject=False),
        "fin": RecordStep("fin", recorder),
    }
    spec = {
        "steps": [
            {"id": "seed", "per_subject": False, "next": "per"},
            {"id": "per", "next": "barrier"},
            {"id": "barrier", "per_subject": False, "next": "fin"},
            {"id": "fin", "next": None},
        ],
        "max_workers": 3,
    }
    engine, report = build_engine(tmp_path, spec, steps)
    engine.run()

    order = recorder.order()
    barrier_start = order.index(("start", "barrier", None))
    per_ends = [i for i, (p, n, s) in enumerate(order) if p == "end" and n == "per"]
    assert all(
        i < barrier_start for i in per_ends
    )  # all per-subject work finished first
    assert recorder.runs("barrier") == [None]  # ran exactly once
    for s in ["s1", "s2", "s3"]:
        assert report.is_done(s)


def test_on_error_stop_raises(tmp_path):
    from ._helpers import Recorder

    recorder = Recorder()
    steps = {
        "seed": SeedStep(["s1", "s2"]),
        "work": RecordStep("work", recorder, fail_for=["s2"]),
    }
    spec = {
        "steps": [
            {"id": "seed", "per_subject": False, "next": "work"},
            {"id": "work", "on_error": "stop", "next": None},
        ]
    }
    engine, _ = build_engine(tmp_path, spec, steps)
    with pytest.raises(RuntimeError, match="boom"):
        engine.run()


def test_on_error_ignore_skips_subject(tmp_path):
    from ._helpers import Recorder

    recorder = Recorder()
    steps = {
        "seed": SeedStep(["s1", "s2", "s3"]),
        "work": RecordStep("work", recorder, fail_for=["s2"]),
        "barrier": RecordStep("barrier", recorder, per_subject=False),
        "fin": RecordStep("fin", recorder),
    }
    spec = {
        "steps": [
            {"id": "seed", "per_subject": False, "next": "work"},
            {"id": "work", "on_error": "ignore", "next": "barrier"},
            {"id": "barrier", "per_subject": False, "next": "fin"},
            {"id": "fin", "next": None},
        ]
    }
    engine, report = build_engine(tmp_path, spec, steps)
    engine.run()  # does not raise
    # the barrier fired for the two good subjects despite s2 failing
    assert recorder.runs("barrier") == [None]
    assert report.is_done("s1") and report.is_done("s3")
    assert not report.is_done("s2")

    data = yaml.safe_load(open(str(tmp_path / "report.yaml")))
    assert data["status"]["s2"] < 0  # recorded as an error


def test_prepare_entrypoint_stops_before_sanity_check(tmp_path):
    from ._helpers import Recorder

    recorder = Recorder()
    steps = {
        "seed": SeedStep(["s1", "s2"]),
        "prepare": RecordStep("prepare", recorder),
        "SanityCheck": RecordStep("sanity", recorder, per_subject=False),
        "Statistics": RecordStep("statistics", recorder, per_subject=False),
    }
    spec = {
        "steps": [
            {"id": "seed", "per_subject": False, "next": "prepare"},
            # YAML keeps the graph continuous, but prepare must stop here.
            {"id": "prepare", "next": "sanity_check"},
            {
                "id": "sanity_check",
                "step": "SanityCheck",
                "per_subject": False,
                "next": "statistics",
            },
            {
                "id": "statistics",
                "step": "Statistics",
                "per_subject": False,
                "next": None,
            },
        ],
    }
    engine, report = build_engine(tmp_path, spec, steps)
    engine.run("prepare")

    assert sorted(recorder.runs("prepare")) == ["s1", "s2"]
    assert recorder.runs("sanity") == []
    assert recorder.runs("statistics") == []
    assert report.is_done("s1") and report.is_done("s2")


def test_sanity_check_entrypoint_skips_preparation(tmp_path):
    from ._helpers import Recorder

    recorder = Recorder()
    steps = {
        "seed": SeedStep(["unused"]),
        "prepare": RecordStep("prepare", recorder),
        "SanityCheck": RecordStep("sanity", recorder, per_subject=False),
        "Statistics": RecordStep("statistics", recorder, per_subject=False),
    }
    spec = {
        "steps": [
            {"id": "seed", "per_subject": False, "next": "prepare"},
            {"id": "prepare", "next": "sanity_check"},
            {
                "id": "sanity_check",
                "step": "SanityCheck",
                "per_subject": False,
                "next": "statistics",
            },
            {
                "id": "statistics",
                "step": "Statistics",
                "per_subject": False,
                "next": None,
            },
        ],
    }
    engine, _ = build_engine(tmp_path, spec, steps)
    engine.run("sanity_check", resume=False)

    assert recorder.runs("prepare") == []
    assert recorder.runs("sanity") == [None]
    assert recorder.runs("statistics") == [None]


def test_resume_skips_completed_steps(tmp_path):
    from ._helpers import Recorder

    recorder = Recorder()
    # Pre-seed a report as if 'a' already ran for both subjects and they're at 'b'
    paths = make_paths(tmp_path)
    seeded = Report(paths.report_file)
    seeded.add_subject("s1", node="b")
    seeded.add_subject("s2", node="b")
    seeded.flush()

    steps = {
        "seed": SeedStep(["s1", "s2"]),  # should NOT run on resume
        "a": RecordStep("a", recorder),  # should NOT run on resume
        "b": RecordStep("b", recorder),
        "c": RecordStep("c", recorder),
    }
    spec = {
        "steps": [
            {"id": "seed", "per_subject": False, "next": "a"},
            {"id": "a", "next": "b"},
            {"id": "b", "next": "c"},
            {"id": "c", "next": None},
        ]
    }
    engine, report = build_engine(tmp_path, spec, steps)
    engine.run()

    assert recorder.runs("a") == []  # resumed past 'a'
    assert sorted(recorder.runs("b")) == ["s1", "s2"]
    assert sorted(recorder.runs("c")) == ["s1", "s2"]
    assert report.is_done("s1") and report.is_done("s2")
