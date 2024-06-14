import logging
from typing import Union

import medperf.config as config
from medperf.entities.cube import Cube
from medperf.entities.edit_cube import EditCubeData


class EditCube:
    @classmethod
    def run(cls, cube_uid: Union[str, int], mlcube_partial_info: EditCubeData):
        """Update mlcube in the development mode on the medperf server

        Args:
            cube_uid: uid of cube to modify
            mlcube_partial_info (dict): Dictionary containing the modified fields.
        """
        ui = config.ui

        logging.debug("Downloading initial MLCube..")
        edition = cls(cube_uid, mlcube_partial_info)
        logging.debug("Validating MLCube DEVELOPMENT state..")
        edition.validate_dev_state()

        with ui.interactive():
            ui.text = "Validating updated MLCube can be downloaded"
            logging.debug("Applying MLCube edit..")
            edition.apply()
            ui.text = "Submitting MLCube edit to MedPerf"
            logging.debug("Uploading MLCube..")
            edition.upload()
            edition.write()

    def __init__(self, cube_uid: Union[str, int], edit_info: EditCubeData):
        self.ui = config.ui
        self.cube = Cube.get(cube_uid)
        self.edit_info = edit_info

    def validate_dev_state(self):
        if self.cube.state != "DEVELOPMENT":
            raise ValueError("Only cubes in development state can be edited")

    def apply(self):
        cube = self.cube
        new = self.edit_info

        if new.name:
            cube.name = new.name

        if new.git_mlcube_url:
            cube.git_mlcube_url = new.git_mlcube_url

        if new.git_mlcube_hash:
            cube.git_mlcube_hash = new.git_mlcube_hash
        elif new.git_mlcube_url is not None:
            cube.git_mlcube_hash = ""

        if new.git_parameters_url:
            cube.git_parameters_url = new.git_parameters_url

        if new.parameters_hash:
            cube.parameters_hash = new.parameters_hash
        elif new.git_parameters_url is not None:
            cube.parameters_hash = ""

        if new.image_tarball_url:
            cube.image_tarball_url = new.image_tarball_url

        if new.image_tarball_hash:
            cube.image_tarball_hash = new.image_tarball_hash
        elif new.image_tarball_url is not None:
            cube.image_tarball_hash = ""

        if new.additional_files_tarball_url:
            cube.additional_files_tarball_url = new.additional_files_tarball_url

        if new.additional_files_tarball_hash:
            cube.additional_files_tarball_hash = new.additional_files_tarball_hash
        elif new.additional_files_tarball_url is not None:
            cube.additional_files_tarball_hash = ""

        self.download()

        if new.git_mlcube_hash == "":
            new.git_mlcube_hash = cube.git_mlcube_hash
        if new.parameters_hash == "":
            new.parameters_hash = cube.parameters_hash
        if new.image_tarball_hash == "":
            new.image_tarball_hash = cube.image_tarball_hash
        if new.additional_files_tarball_hash == "":
            new.additional_files_tarball_hash = cube.additional_files_tarball_hash

    def download(self):
        logging.debug("removing from filesystem...")
        self.cube.remove_from_filesystem()
        logging.debug("download config files..")
        self.cube.download_config_files()
        logging.debug("download run files..")
        self.cube.download_run_files()

    def upload(self):
        updated_body = Cube.edit(self.cube.id, self.edit_info)
        self.cube = Cube(**updated_body)

    def write(self):
        self.cube.write()
