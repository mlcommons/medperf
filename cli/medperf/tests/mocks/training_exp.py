from typing import Optional
from medperf.enums import Status
from medperf.entities.training_exp import TrainingExp


class TestTrainingExp(TrainingExp):
    __test__ = False
    id: Optional[int] = 1
    name: str = "name"
    demo_dataset_tarball_url: str = "tarball_url"
    demo_dataset_tarball_hash: str = "tarball_hash"
    data_preparation_mlcube: int = 1
    fl_mlcube: int = 2
    fl_admin_mlcube: int = 3
    approval_status: Status = Status.APPROVED
