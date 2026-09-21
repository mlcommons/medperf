import sys
import textwrap

import pytest

from prep_workflow.discovery import (
    DiscoveryError,
    add_to_path,
    discover_conditions,
    discover_steps,
)


def _write_package(root, package, files):
    pkg_dir = root / package
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    for filename, content in files.items():
        (pkg_dir / filename).write_text(textwrap.dedent(content))


def _fresh_import(tmp_path, package):
    add_to_path(str(tmp_path))
    for mod in list(sys.modules):
        if mod == package or mod.startswith(package + "."):
            del sys.modules[mod]


def test_discovers_multiple_classes_across_files(tmp_path, monkeypatch):
    _write_package(
        tmp_path,
        "steps_a",
        {
            "one.py": """
                from prep_workflow import Step
                class First(Step):
                    def run(self, ctx): pass
                class Second(Step):
                    per_subject = False
                    def run(self, ctx): pass
            """,
            "two.py": """
                from prep_workflow import Step
                class Third(Step):
                    name = "renamed_third"
                    def run(self, ctx): pass
            """,
        },
    )
    _fresh_import(tmp_path, "steps_a")
    found = discover_steps("steps_a")
    assert set(found) == {"First", "Second", "renamed_third"}


def test_discovers_conditions(tmp_path):
    _write_package(
        tmp_path,
        "conds_a",
        {
            "c.py": """
                from prep_workflow import Condition
                class Ready(Condition):
                    def evaluate(self, ctx): return True
            """
        },
    )
    _fresh_import(tmp_path, "conds_a")
    found = discover_conditions("conds_a")
    assert set(found) == {"Ready"}


def test_duplicate_names_raise(tmp_path):
    _write_package(
        tmp_path,
        "steps_dup",
        {
            "a.py": """
                from prep_workflow import Step
                class Dup(Step):
                    def run(self, ctx): pass
            """,
            "b.py": """
                from prep_workflow import Step
                class Dup(Step):
                    def run(self, ctx): pass
            """,
        },
    )
    _fresh_import(tmp_path, "steps_dup")
    with pytest.raises(DiscoveryError, match="share the name"):
        discover_steps("steps_dup")


def test_abstract_intermediate_bases_are_skipped(tmp_path):
    _write_package(
        tmp_path,
        "steps_abstract",
        {
            "a.py": """
                from abc import abstractmethod
                from prep_workflow import Step
                class MiddleBase(Step):
                    @abstractmethod
                    def extra(self): ...
                class Concrete(MiddleBase):
                    def run(self, ctx): pass
                    def extra(self): pass
            """
        },
    )
    _fresh_import(tmp_path, "steps_abstract")
    found = discover_steps("steps_abstract")
    assert set(found) == {"Concrete"}  # MiddleBase (still abstract) skipped
