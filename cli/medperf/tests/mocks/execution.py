from typing import Optional
from medperf.entities.execution import Execution


class TestExecution(Execution):
    id: Optional[int] = 1
    name: str = "name"
    benchmark: int = 1
    model: int = 1
    dataset: int = 1
    results: dict = {}
