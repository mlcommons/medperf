from typing import Optional
from medperf.entities.cube import Cube


EMPTY_FILE_HASH = "da39a3ee5e6b4b0d3255bfef95601890afd80709"


class TestCube(Cube):
    id: Optional[int] = 1
    name: str = "name"
    git_mlcube_url: str = "https://test.com/mlcube.yaml"
    mlcube_hash: Optional[str] = EMPTY_FILE_HASH
    git_parameters_url: Optional[str] = "https://test.com/parameters.yaml"
    parameters_hash: Optional[str] = EMPTY_FILE_HASH
    image_tarball_url: Optional[str] = "https://test.com/image.tar.gz"
    image_tarball_hash: Optional[str] = EMPTY_FILE_HASH
    additional_files_tarball_url: Optional[str] = (
        "https://test.com/additional_files.tar.gz"
    )
    additional_files_tarball_hash: Optional[str] = EMPTY_FILE_HASH
    stages_url: Optional[str] = "https://test.com/stages.yaml"
    stages_hash: Optional[str] = EMPTY_FILE_HASH
    state: str = "OPERATION"
    is_valid = True
