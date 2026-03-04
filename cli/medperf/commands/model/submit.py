import os

from git import Optional

import medperf.config as config
from medperf.entities.model import Model
from medperf.exceptions import InvalidArgumentError
from medperf.utils import remove_path
from medperf.enums import ModelType
from medperf.commands.mlcube.submit import SubmitCube
from medperf.commands.asset.submit import SubmitAsset

"""
    container_info = {
        "name": name,
        "image_hash": image_hash,
        "additional_files_tarball_url": additional_file,
        "additional_files_tarball_hash": additional_hash,
        "state": "OPERATION" if operational else "DEVELOPMENT",
    }
    SubmitCube.run(
        mlcube_info,
        container_config=container_config_file,
        parameters_config=parameters_file,
        decryption_key=decryption_key,
    )
    SubmitAsset.run(
        name=name,
        asset_path=asset_path,
        asset_url=asset_url,
        operational=operational,
    )
"""


class SubmitModel:
    @classmethod
    def run(
        cls,
        name: str,
        operational: bool,
        container_config_file: Optional[str],
        parameters_config_file: Optional[str],
        additional_file: Optional[str],
        additional_hash: Optional[str],
        image_hash: Optional[str],
        decryption_key: Optional[str],
        asset_path: Optional[str],
        asset_url: Optional[str],
    ):
        """Submits a new model to the medperf platform.

        A model wraps either a container or a file-based asset.

        Args:
            name (str): Name of the model.
            container_config_file (Optional[str]): Path to the container config file (for CONTAINER type).
            parameters_config_file (Optional[str]): Path to the parameters config file (for CONTAINER type).
            additional_file (Optional[str]): Path to the additional files tarball (for CONTAINER type).
            additional_hash (Optional[str]): Hash of the additional files tarball (for CONTAINER type).
            image_hash (Optional[str]): Hash of the image file (for CONTAINER type).
            decryption_key (Optional[str]): Path to the decryption key file (for encrypted containers).
            asset_path (Optional[str]): Path to the asset file (for ASSET type).
            asset_url (Optional[str]): URL to download the asset from (for ASSET type).
            operational (bool): Whether to submit as OPERATIONAL state.
        """
        ui = config.ui
        submission = cls(
            name,
            operational,
            container_config_file,
            parameters_config_file,
            additional_file,
            additional_hash,
            image_hash,
            decryption_key,
            asset_path,
            asset_url,
        )
        submission.validate_inputs()

        with ui.interactive():
            ui.text = "Submitting model to MedPerf"
            if submission.model_type == ModelType.CONTAINER.value:
                submission.prepare_container_submission()
                submission.create_model_object()
                updated_model_body, updated_container_body = submission.upload()
                submission.finalize_container_submission(updated_container_body)
            else:
                submission.prepare_asset_submission()
                submission.create_model_object()
                updated_model_body, updated_asset_body = submission.upload()
                submission.finalize_asset_submission(updated_asset_body)
            submission.to_permanent_path(updated_model_body)
            submission.write(updated_model_body)

        ui.print(f"Model registered with UID: {submission.model.id}")
        return submission.model.id

    def __init__(
        self,
        name,
        operational,
        container_config_file,
        parameters_config_file,
        additional_file,
        additional_hash,
        image_hash,
        decryption_key,
        asset_path,
        asset_url,
    ):
        self.name = name
        self.container_config_file = container_config_file
        self.parameters_config_file = parameters_config_file
        self.additional_file = additional_file
        self.additional_hash = additional_hash
        self.image_hash = image_hash
        self.decryption_key = decryption_key
        self.asset_path = asset_path
        self.asset_url = asset_url
        self.operational = operational
        self.model = None
        self.model_type = None
        self.subentity_submission = None

    def validate_inputs(self):
        container_provided = (
            self.container_config_file
            or self.parameters_config_file
            or self.additional_file
            or self.additional_hash
            or self.image_hash
        )
        asset_provided = self.asset_path or self.asset_url
        if container_provided and asset_provided:
            raise InvalidArgumentError(
                "Cannot provide both container and asset information for a model."
            )
        if not container_provided and not asset_provided:
            raise InvalidArgumentError(
                "Must provide either container information or asset information for a model."
            )
        if container_provided:
            if not self.container_config_file:
                raise InvalidArgumentError(
                    "Container config file is required for container-backed model."
                )
        self.model_type = (
            ModelType.CONTAINER.value if container_provided else ModelType.ASSET.value
        )

    def prepare_container_submission(self):
        submit_info = {
            "name": self.name,
            "image_hash": self.image_hash,
            "additional_files_tarball_url": self.additional_file,
            "additional_files_tarball_hash": self.additional_hash,
            "state": "OPERATION" if self.operational else "DEVELOPMENT",
        }
        ui = config.ui
        submission = SubmitCube(
            submit_info,
            self.container_config_file,
            self.parameters_config_file,
            self.decryption_key,
        )
        submission.read_config_files()
        submission.create_cube_object()

        ui.text = "Validating Container can be downloaded"
        submission.validate()
        submission.download_run_files()
        self.subentity_submission = submission

    def prepare_asset_submission(self):
        ui = config.ui
        submission = SubmitAsset(
            self.name, self.asset_path, self.asset_url, self.operational
        )
        submission.validate_inputs()

        ui.text = "Preparing asset"
        submission.prepare_asset()
        submission.create_asset_object()
        submission.validate_asset_file()
        self.subentity_submission = submission

    def create_model_object(self):
        state = "OPERATION" if self.operational else "DEVELOPMENT"
        container = None
        asset = None
        if self.model_type == ModelType.CONTAINER.value:
            container = self.subentity_submission.cube
        else:
            asset = self.subentity_submission.asset

        self.model = Model(
            name=self.name,
            type=self.model_type,
            container=container,
            asset=asset,
            state=state,
        )
        config.tmp_paths.append(self.model.path)
        os.makedirs(self.model.path, exist_ok=True)

    def upload(self):
        updated_body = self.model.upload()
        subentity_body = (
            updated_body["container"]
            if self.model_type == ModelType.CONTAINER.value
            else updated_body["asset"]
        )
        return updated_body, subentity_body

    def finalize_container_submission(self, updated_body: dict):
        self.subentity_submission.to_permanent_path(updated_body)
        self.subentity_submission.write(updated_body)
        self.subentity_submission.store_decryption_key()

    def finalize_asset_submission(self, updated_body: dict):
        self.subentity_submission.to_permanent_path(updated_body)
        self.subentity_submission.write(updated_body)

    def to_permanent_path(self, model_dict):
        old_path = self.model.path
        updated_model = Model(**model_dict)
        new_path = updated_model.path
        remove_path(new_path)
        os.rename(old_path, new_path)

    def write(self, updated_body):
        self.model = Model(**updated_body)
        self.model.write()
