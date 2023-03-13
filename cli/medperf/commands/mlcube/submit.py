import os
import shutil

import medperf.config as config
from medperf.entities.cube import Cube
from medperf.utils import storage_path
from medperf.exceptions import InvalidEntityError


class SubmitCube:
    @classmethod
    def run(cls, submit_info: dict):
        """Submits a new cube to the medperf platform

        Args:
            submit_info (dict): Dictionary containing the cube information.
        """
        ui = config.ui
        submission = cls(submit_info)

        with ui.interactive():
            ui.text = "Validating MLCube can be downloaded"
            submission.download()
            ui.text = "Submitting MLCube to MedPerf"
            updated_cube_dict = submission.upload()
            submission.to_permanent_path(updated_cube_dict)
            submission.write(updated_cube_dict)

    def __init__(self, submit_info: dict):
        self.comms = config.comms
        self.ui = config.ui
        self.submit_info = submit_info

    def download(self):
        self.cube = Cube(**self.submit_info)
        self.cube.download()
        if not self.cube.valid():
            raise InvalidEntityError("MLCube hash check failed. Submission aborted.")

    def upload(self):
        updated_body = self.cube.upload()
        return updated_body

    def to_permanent_path(self, cube_dict):
        """Renames the temporary cube submission to a permanent one using the uid of
        the registered cube
        """
        cube = Cube(**cube_dict)
        cubes_storage = storage_path(config.cubes_storage)
        old_cube_loc = os.path.join(cubes_storage, cube.generated_uid)
        new_cube_loc = cube.path
        if os.path.exists(new_cube_loc):
            shutil.rmtree(new_cube_loc)
        os.rename(old_cube_loc, new_cube_loc)

    def write(self, updated_cube_dict):
        cube = Cube(**updated_cube_dict)
        cube.write()
