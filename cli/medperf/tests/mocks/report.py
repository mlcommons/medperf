from medperf.entities.report import TestReport


class TestTestReport(TestReport):
    __test__ = False

    def __init__(self, **kwargs):
        defaults = {
            "demo_dataset_url": "url",
            "demo_dataset_hash": "hash",
            "prepared_data_hash": None,
            "data_preparation_mlcube": 1,
            "model": 2,
            "data_evaluator_mlcube": 3,
            "results": {"acc": 1},
        }
        defaults.update(kwargs)
        super().__init__(**defaults)
