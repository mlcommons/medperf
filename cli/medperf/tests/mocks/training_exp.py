from medperf.enums import Status
from medperf.entities.training_exp import TrainingExp


class TestTrainingExp(TrainingExp):
    __test__ = False

    def __init__(self, **kwargs):
        defaults = {
            "id": 1,
            "name": "name",
            "demo_dataset_tarball_url": "tarball_url",
            "demo_dataset_tarball_hash": "tarball_hash",
            "data_preparation_mlcube": 1,
            "fl_mlcube": 2,
            "fl_admin_mlcube": 3,
            "approval_status": Status.APPROVED,
        }
        defaults.update(kwargs)
        super().__init__(**defaults)
