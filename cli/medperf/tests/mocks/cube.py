from pydantic import HttpUrl
from typing import Optional
from medperf.entities.cube import Cube


EMPTY_FILE_HASH = "da39a3ee5e6b4b0d3255bfef95601890afd80709"


class MockCube:
    def __init__(self, is_valid):
        self.name = "Test"
        self.is_valid = is_valid
        self.id = "1"

    def valid(self):
        return self.is_valid

    def run(self):
        pass

    def get_default_output(self, *args, **kwargs):
        return "out_path"


class TestCube(Cube):
    id: int = 1
    name: str = "name"
    git_mlcube_url: HttpUrl = "https://test.com/mlcube.yaml"
    mlcube_hash: Optional[str] = EMPTY_FILE_HASH
    git_parameters_url: Optional[HttpUrl] = "https://test.com/parameters.yaml"
    parameters_hash: Optional[str] = EMPTY_FILE_HASH
    image_tarball_url: Optional[HttpUrl] = "https://test.com/image.tar.gz"
    image_tarball_hash: Optional[str] = EMPTY_FILE_HASH
    additional_files_tarball_url: Optional[
        HttpUrl
    ] = "https://test.com/additional_files.tar.gz"
    additional_files_tarball_hash: Optional[str] = EMPTY_FILE_HASH
    state: str = "PRODUCTION"
