from medperf.entities.cube import Cube


EMPTY_FILE_HASH = "da39a3ee5e6b4b0d3255bfef95601890afd80709"


class TestCube(Cube):
    __test__ = False

    def __init__(self, **kwargs):
        defaults = {
            "id": 1,
            "name": "name",
            "container_config": {"key": "value"},
            "parameters_config": {"parameter": "value"},
            "additional_files_tarball_url": "https://test.com/additional_files.tar.gz",
            "additional_files_tarball_hash": EMPTY_FILE_HASH,
            "state": "OPERATION",
            "is_valid": True,
        }
        defaults.update(kwargs)
        super().__init__(**defaults)
