from medperf.entities.model import Model


class TestModel(Model):
    __test__ = False

    def __init__(self, **kwargs):
        defaults = {
            "id": 1,
            "name": "name",
            "state": "OPERATION",
            "is_valid": True,
            "type": "CONTAINER",
            "container": {
                "id": 1,
                "name": "container-name",
                "container_config": {"key": "value"},
                "parameters_config": {"parameter": "value"},
                "additional_files_tarball_url": None,
                "state": "OPERATION",
                "is_valid": True,
            },
            "asset": None,
        }
        defaults.update(kwargs)
        super().__init__(**defaults)
