import validators

from medperf.ui import UI
from medperf import config
from medperf.comms import Comms
from medperf.utils import get_file_sha1


class SubmitCube:
    @classmethod
    def run(cls, comms: Comms, ui: UI):
        """Submits a new cube to the medperf platform

        Args:
            comms (Comms): Communication instance
            ui (UI): UI instance
        """
        submission = cls(comms, ui)
        submission.get_information()
        while not submission.is_valid():
            submission.get_information()

        with ui.interactive():

            if submission.additional_file:
                ui.text = "Generating additional file hash"
                submission.get_additional_hash()
                ui.print("Additional file hash generated")
            if submission.image_file:
                ui.text = "Generating image file hash"
                submission.get_image_hash()
                ui.print("Image file hash generated")
            ui.text = "Submitting MLCube to MedPerf"
            submission.submit()
        ui.print("Uploaded")

    def __init__(self, comms: Comms, ui: UI):
        self.comms = comms
        self.ui = ui
        self.name = None
        self.mlcube_file = None
        self.params_file = None
        self.additional_file = None
        self.additional_hash = None
        self.image_file = None
        self.image_hash = None

    def get_information(self):
        name_prompt = "MLCube name: "
        mlcube_file_prompt = (
            f"MLCube manifest file URL (must start with {config.git_file_domain}): "
        )
        params_file_prompt = f"Parameters file URL (must start with {config.git_file_domain}) [OPTIONAL]: "
        additional_file_prompt = "Additional files tarball URL [OPTIONAL]: "
        image_file_prompt = "Image URL [OPTIONAL]: "

        self.__get_or_print("name", name_prompt)
        self.__get_or_print("mlcube_file", mlcube_file_prompt)
        self.__get_or_print("params_file", params_file_prompt)
        self.__get_or_print("additional_file", additional_file_prompt)
        self.__get_or_print("image_file", image_file_prompt)

    def __get_or_print(self, attr, prompt):
        attr_val = getattr(self, attr)
        if attr_val is None or attr_val == "":
            setattr(self, attr, self.ui.prompt(prompt))
        else:
            self.ui.print(prompt + attr_val)

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

    def get_additional_hash(self):
        tmp_cube_uid = "tmp_submission"
        add_file_path = self.comms.get_cube_additional(
            self.additional_file, tmp_cube_uid
        )
        self.additional_hash = get_file_sha1(add_file_path)

    def get_image_hash(self):
        tmp_cube_uid = "tmp_submission"
        image_path = self.comms.get_cube_image(self.image_file, tmp_cube_uid)
        self.image_hash = get_file_sha1(image_path)

    def todict(self):
        dict = {
            "name": self.name,
            "git_mlcube_url": self.mlcube_file,
            "git_parameters_url": self.params_file,
            "state": "OPERATION",
            "is_valid": True,
        }
        if self.image_file:
            dict["image_tarball_url"] = self.image_file
            dict["image_tarball_hash"] = self.image_hash
        if self.additional_file:
            dict["additional_files_tarball_url"] = self.additional_file
            dict["additional_files_tarball_hash"] = self.additional_hash
        return dict

    def submit(self):
        body = self.todict()
        self.comms.upload_mlcube(body)
