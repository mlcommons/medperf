from medperf.entities.execution import Execution


class TestExecution(Execution):
    __test__ = False

    def __init__(self, **kwargs):
        defaults = {
            "id": 1,
            "name": "name",
            "benchmark": 1,
            "model": 1,
            "dataset": 1,
            "results": {},
        }
        defaults.update(kwargs)
        super().__init__(**defaults)

    def upload(self):
        return self.todict()
