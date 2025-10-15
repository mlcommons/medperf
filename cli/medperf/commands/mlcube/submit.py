import os
from typing import Optional
import medperf.config as config
from medperf.entities.cube import Cube
from medperf.utils import remove_path
from medperf.comms.entity_resources.utils import load_yaml_content


class SubmitCube:
    @classmethod
    def run(cls, submit_info: dict, container_config: str, parameters_config: Optional[str] = None):
        """Submits a new cube to the medperf platform

        Args:
            submit_info (dict): Dictionary containing the cube information.
        """
        ui = config.ui

        cls.add_yaml_info_to_submit_info(yaml_path=container_config,
                                         submit_info=submit_info,
                                         key='container_config')
        if parameters_config is not None:
            cls.add_yaml_info_to_submit_info(yaml_path=parameters_config,
                                             submit_info=submit_info,
                                             key='parameters_config')
        submission = cls(submit_info)

        with ui.interactive():
            ui.text = "Validating Container can be downloaded"
            submission.download()
            ui.text = "Submitting Container to MedPerf"
            updated_cube_dict = submission.upload()
            submission.to_permanent_path(updated_cube_dict)
            submission.write(updated_cube_dict)
        return submission.cube.id

    @staticmethod
    def add_yaml_info_to_submit_info(yaml_path: str, submit_info: dict, key: str):
        """Note: modifies submit_info!"""
        yaml_content = load_yaml_content(yaml_path)
        submit_info[key] = yaml_content

    def __init__(self, submit_info: dict):
        self.comms = config.comms
        self.ui = config.ui
        self.cube = Cube(**submit_info)
        config.tmp_paths.append(self.cube.path)

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
