from typing import Optional
from medperf.entities.cube import Cube


EMPTY_FILE_HASH = "da39a3ee5e6b4b0d3255bfef95601890afd80709"


class MockCube:
    def __init__(self, is_valid, id=1, report_specified=False):
        self.name = "Test"
        self.is_valid = is_valid
        self.id = id
        self.report_specified = report_specified

    def valid(self):
        return self.is_valid

    def run(self):
        pass

    def get_default_output(self, *args, **kwargs):
        if args == ("prepare", "report_file") and not self.report_specified:
            return None
        return "out_path"

    @property
    def identifier(self):
        return self.id or self.name


class TestCube(Cube):
    id: Optional[int] = 1
    name: str = "name"
    git_mlcube_url: str = "https://test.com/mlcube.yaml"
    mlcube_hash: Optional[str] = EMPTY_FILE_HASH
    git_parameters_url: Optional[str] = "https://test.com/parameters.yaml"
    parameters_hash: Optional[str] = EMPTY_FILE_HASH
    image_tarball_url: Optional[str] = "https://test.com/image.tar.gz"
    image_tarball_hash: Optional[str] = EMPTY_FILE_HASH
    additional_files_tarball_url: Optional[
        str
    ] = "https://test.com/additional_files.tar.gz"
    additional_files_tarball_hash: Optional[str] = EMPTY_FILE_HASH
    state: str = "PRODUCTION"
