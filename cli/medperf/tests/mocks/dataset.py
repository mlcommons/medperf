from medperf.enums import Status
from medperf.entities.dataset import Dataset


class TestDataset(Dataset):
    __test__ = False

    def __init__(self, **kwargs):
        defaults = {
            "id": 1,
            "name": "name",
            "location": "location",
            "data_preparation_mlcube": 1,
            "input_data_hash": "input_data_hash",
            "generated_uid": "generated_uid",
            "generated_metadata": {},
            "status": Status.APPROVED.value,
            "state": "OPERATION",
            "submitted_as_prepared": False,
        }
        defaults.update(kwargs)
        super().__init__(**defaults)
