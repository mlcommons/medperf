from typing import Optional
from medperf.entities.cube import Cube


EMPTY_FILE_HASH = "da39a3ee5e6b4b0d3255bfef95601890afd80709"


class TestCube(Cube):
    __test__ = False
    id: Optional[int] = 1
    name: str = "name"
    container_config: dict = {"key": "value"}
    parameters_config: Optional[dict] = {"parameter": "value"}
    image_tarball_url: Optional[str] = "https://test.com/image.tar.gz"
    image_tarball_hash: Optional[str] = EMPTY_FILE_HASH
    additional_files_tarball_url: Optional[str] = (
        "https://test.com/additional_files.tar.gz"
    )
    additional_files_tarball_hash: Optional[str] = EMPTY_FILE_HASH
    state: str = "OPERATION"
    is_valid = True
