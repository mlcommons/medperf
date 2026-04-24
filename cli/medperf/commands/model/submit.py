from typing import Optional
from medperf.exceptions import InvalidArgumentError
from medperf.commands.mlcube.submit import SubmitCube
from medperf.commands.asset.submit import SubmitAsset


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
        if submission.is_container:
            return submission.run_container_submission()
        return submission.run_asset_submission()

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
        self.is_container: bool = None

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
        self.is_container = container_provided

    def run_container_submission(self):
        submit_info = {
            "name": self.name,
            "image_hash": self.image_hash,
            "additional_files_tarball_url": self.additional_file,
            "additional_files_tarball_hash": self.additional_hash,
            "state": "OPERATION" if self.operational else "DEVELOPMENT",
        }
        return SubmitCube.run(
            submit_info,
            self.container_config_file,
            self.parameters_config_file,
            self.decryption_key,
        )

    def run_asset_submission(self):
        return SubmitAsset.run(
            self.name, self.asset_path, self.asset_url, self.operational
        )
