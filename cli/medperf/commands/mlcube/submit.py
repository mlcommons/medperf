import validators

import medperf.config as config
from medperf.entities.cube import Cube
from medperf.utils import pretty_error


class SubmitCube:
    @classmethod
    def run(cls, submit_info: dict):
        """Submits a new cube to the medperf platform

        Args:
            submit_info (dict): Dictionary containing the cube information.
                expected keys:
                    name,
                    mlcube_file,
                    params_file,
                    additional_files_tarball_url,
                    additional_files_tarball_hash,
                    image_tarball_url,
                    image_tarball_hash,
        """
        ui = config.ui
        submission = cls(submit_info)
        if not submission.is_valid():
            pretty_error("MLCube submission is invalid")

        with ui.interactive():
            ui.text = "Validating MLCube can be downloaded"
            cube = Cube(submission.todict())
            cube.download()
            if submission.additional_file:
                ui.text = "Generating additional file hash"
                submission.additional_hash = cube.additional_hash
                ui.print("Additional file hash generated")
            if submission.image_file:
                ui.text = "Generating image file hash"
                submission.image_tarball_hash = cube.image_tarball_hash
                ui.print("Image file hash generated")
            ui.text = "Submitting MLCube to MedPerf"
            cube.upload()

    def __init__(self, submit_info: dict):
        self.comms = config.comms
        self.ui = config.ui
        self.name = submit_info["name"]
        self.mlcube_file = submit_info["mlcube_file"]
        self.params_file = submit_info["params_file"]
        self.additional_file = submit_info["additional_files_tarball_url"]
        self.additional_hash = submit_info["additional_files_tarball_hash"]
        self.image_file = submit_info["image_tarball_url"]
        self.image_tarball_hash = submit_info["image_tarball_hash"]

    def is_valid(self):
        name_valid_length = 0 < len(self.name) < 20
        mlcube_file_is_valid = (
            self.mlcube_file.startswith(config.git_file_domain)
            and validators.url(self.mlcube_file)
            and self.mlcube_file.endswith(".yaml")
        )
        params_file_is_valid = self.params_file == "" or (
            self.params_file.startswith(config.git_file_domain)
            and validators.url(self.params_file)
            and self.params_file.endswith(".yaml")
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

    def todict(self):
        dict = {
            "name": self.name,
            "git_mlcube_url": self.mlcube_file,
            "git_parameters_url": self.params_file,
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
