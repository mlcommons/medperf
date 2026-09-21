"""Automatic discovery of ``Step`` and ``Condition`` classes.

The author drops classes into the ``steps`` and ``conditions`` packages (any
number of files, any number of classes per file). We import every submodule and
collect the concrete subclasses, indexed by their registered name.
"""

from __future__ import annotations

import importlib
import inspect
import os
import pkgutil
import sys
from typing import Dict, Type, TypeVar

from prep_workflow.base import Condition, Step, registered_name

T = TypeVar("T")


class DiscoveryError(Exception):
    pass


def add_to_path(directory: str) -> None:
    """Make sibling packages under ``directory`` importable (e.g. /project)."""
    directory = os.path.abspath(directory)
    if directory not in sys.path:
        sys.path.insert(0, directory)


def _collect(package_name: str, base: Type[T]) -> Dict[str, Type[T]]:
    package = importlib.import_module(package_name)
    found: Dict[str, Type[T]] = {}
    modules = pkgutil.walk_packages(package.__path__, prefix=package.__name__ + ".")
    for module_info in modules:
        module = importlib.import_module(module_info.name)
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if not issubclass(obj, base) or obj is base:
                continue
            if inspect.isabstract(obj):  # skip intermediate abstract bases
                continue
            name = registered_name(obj)
            existing = found.get(name)
            if existing is not None and existing is not obj:
                raise DiscoveryError(
                    f"two {base.__name__} classes share the name '{name}': "
                    f"{existing.__module__}.{existing.__qualname__} and "
                    f"{obj.__module__}.{obj.__qualname__}"
                )
            found[name] = obj
    return found


def discover_steps(package_name: str = "steps") -> Dict[str, Type[Step]]:
    return _collect(package_name, Step)


def discover_conditions(package_name: str = "conditions") -> Dict[str, Type[Condition]]:
    return _collect(package_name, Condition)
