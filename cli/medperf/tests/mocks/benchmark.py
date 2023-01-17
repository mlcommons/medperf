from typing import List
from medperf.enums import Status
from medperf.entities.models import BenchmarkModel


class Benchmark:
    def __init__(self):
        self.name = "MockedBenchmark"
        self.data_preparation = 1


class TestBenchmarkModel(BenchmarkModel):
    id: int = 1
    name: str = "name"
    demo_dataset_tarball_hash: str = "tarball_hash"
    data_preparation_mlcube: int = 1
    reference_model_mlcube: int = 2
    data_evaluator_mlcube: int = 3
    models: List[int] = [2]
    approval_status: Status = Status.APPROVED
