import os
import shutil
import validators

import medperf.config as config
from medperf.entities.cube import Cube
from medperf.utils import storage_path
from medperf.exceptions import InvalidArgumentError, InvalidEntityError


class SubmitCube:
    @classmethod
    def run(cls, submit_info: dict):
        """Submits a new cube to the medperf platform

        Args:
            submit_info (dict): Dictionary containing the cube information.
                expected keys:
                    name,
                    mlcube_file,
                    mlcube_hash
                    params_file,
                    params_hash
                    additional_files_tarball_url,
                    additional_files_tarball_hash,
                    image_tarball_url,
                    image_tarball_hash,
        """
        ui = config.ui
        submission = cls(submit_info)
        if not submission.is_valid():
            raise InvalidArgumentError("MLCube submission is invalid")

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
        self.name = submit_info["name"]
        self.mlcube_file = submit_info["mlcube_file"]
        self.mlcube_hash = submit_info["mlcube_hash"]
        self.params_file = submit_info["params_file"]
        self.parameters_hash = submit_info["parameters_hash"]
        self.additional_file = submit_info["additional_files_tarball_url"]
        self.additional_hash = submit_info["additional_files_tarball_hash"]
        self.image_file = submit_info["image_tarball_url"]
        self.image_tarball_hash = submit_info["image_tarball_hash"]

    def is_valid(self):
        name_valid_length = 0 < len(self.name) < 20
        mlcube_file_is_valid = validators.url(
            self.mlcube_file
        ) and self.mlcube_file.endswith(".yaml")
        params_file_is_valid = self.params_file == "" or (
            validators.url(self.params_file) and self.params_file.endswith(".yaml")
        )
        add_file_is_valid = self.additional_file == "" or validators.url(
            self.additional_file
        )
        image_file_is_valid = self.image_file == "" or validators.url(self.image_file)

        valid = True
        if not name_valid_length:
            valid = False
            self.name = None
            self.ui.print_error("Name is invalid")
        if not mlcube_file_is_valid:
            valid = False
            self.mlcube_file = None
            self.ui.print_error("MLCube file is invalid")
        if not params_file_is_valid:
            valid = False
            self.params_file = None
            self.ui.print_error("Parameters file is invalid")
        if not add_file_is_valid:
            valid = False
            self.additional_file = None
            self.ui.print_error("Additional file is invalid")
        if not image_file_is_valid:
            valid = False
            self.image_file = None
            self.ui.print_error("Image file is invalid")

        return valid

    def download(self):
        cube = Cube(self.todict())
        cube.download()
        self.additional_hash = cube.additional_hash
        self.image_tarball_hash = cube.image_tarball_hash
        self.mlcube_hash = cube.mlcube_hash
        self.parameters_hash = cube.parameters_hash
        if not cube.valid():
            raise InvalidEntityError("MLCube hash check failed. Submission aborted.")

    def todict(self):
        dict = {
            "name": self.name,
            "git_mlcube_url": self.mlcube_file,
            "mlcube_hash": self.mlcube_hash,
            "git_parameters_url": self.params_file,
            "parameters_hash": self.parameters_hash,
            "image_tarball_url": self.image_file,
            "image_tarball_hash": self.image_tarball_hash,
            "additional_files_tarball_url": self.additional_file,
            "additional_files_tarball_hash": self.additional_hash,
            "state": "OPERATION",
            "is_valid": True,
            "id": config.cube_submission_id,
            "owner": None,
            "metadata": {},
            "user_metadata": {},
            "created_at": None,
            "modified_at": None,
        }
        return dict

    def upload(self):
        body = self.todict()
        updated_body = Cube(body).upload()
        return updated_body

    def to_permanent_path(self, cube_dict):
        """Renames the temporary cube submission to a permanent one using the uid of
        the registered cube
        """
        cube = Cube(cube_dict)
        cubes_storage = storage_path(config.cubes_storage)
        old_cube_loc = os.path.join(cubes_storage, cube.generated_uid)
        new_cube_loc = cube.path
        if os.path.exists(new_cube_loc):
            shutil.rmtree(new_cube_loc)
        os.rename(old_cube_loc, new_cube_loc)

    def write(self, updated_cube_dict):
        cube = Cube(updated_cube_dict)
        cube.write()
