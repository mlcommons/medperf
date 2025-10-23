import os

import medperf.config as config
from medperf.entities.cube import Cube
from medperf.exceptions import InvalidArgumentError
from medperf.utils import remove_path, move_container_key_to_local_storage
from pathlib import Path
from medperf.entities.ca import CA


class SubmitCube:
    @classmethod
    def run(cls, submit_info: dict, decryption_key: str = None):
        """Submits a new cube to the medperf platform

        Args:
            submit_info (dict): Dictionary containing the cube information.
        """
        ui = config.ui
        submission = cls(submit_info, decryption_key)
        submission.validate()
        submission.move_decryption_key()
        with ui.interactive():
            ui.text = "Validating Container can be downloaded"
            submission.download()
            ui.text = "Submitting Container to MedPerf"
            updated_cube_dict = submission.upload()
            submission.to_permanent_path(updated_cube_dict)
            submission.write(updated_cube_dict)
        return submission.cube.id

    def __init__(self, submit_info: dict, decryption_key: str = None):
        self.comms = config.comms
        self.ui = config.ui
        self.cube = Cube(**submit_info)
        self.decryption_key = decryption_key
        config.tmp_paths.append(self.cube.path)

    def validate(self):
        pass

    def move_decryption_key(self):
        if self.decryption_key is None:
            return
        trusted_cas = updated_cube_dict["trusted_cas"]
        cas_list = CA.get_many(trusted_cas)
        for ca in cas_list:
            move_container_key_to_local_storage(
                cube_id=updated_cube_dict["id"],
                ca_name=ca.name,
                decryption_key_path=self.decryption_key,
            )

    def download(self):
        self.cube.download_config_files()
        self.cube.download_run_files()

    def upload(self):
        updated_body = self.cube.upload()
        return updated_body

    def to_permanent_path(self, cube_dict):
        """Renames the temporary cube submission to a permanent one using the uid of
        the registered cube
        """
        old_cube_loc = self.cube.path
        updated_cube = Cube(**cube_dict)
        new_cube_loc = updated_cube.path
        remove_path(new_cube_loc)
        os.rename(old_cube_loc, new_cube_loc)

    def write(self, updated_cube_dict):
        self.cube = Cube(**updated_cube_dict)
        self.cube.write()
