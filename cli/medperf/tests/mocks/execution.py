from typing import Optional
from medperf.entities.execution import Execution


class TestExecution(Execution):
    id: Optional[int] = None
    name: str = "name"
    benchmark: int = 1
    model: int = 1
    dataset: int = 1
    results: dict = {}

    def upload(self):
        self.id = 1
        return self.todict()
