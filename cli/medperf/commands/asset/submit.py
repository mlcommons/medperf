import os
import logging

from medperf.comms.entity_resources import resources
import medperf.config as config
from medperf.entities.asset import Asset
from medperf.exceptions import InvalidArgumentError
from medperf.utils import get_file_hash, remove_path, sanitize_path


class SubmitAsset:
    @classmethod
    def run(
        cls,
        name: str,
        asset_path: str = None,
        asset_url: str = None,
        operational: bool = False,
    ):
        """Submits a new asset to the medperf platform.

        The asset can be provided either as a local file path or a URL.
        The file is hashed and stored locally for later use (e.g., mounting
        to evaluator containers). The hash and URL are uploaded to the server.

        Args:
            name (str): Name of the asset.
            asset_path (str): Local path to the asset file.
            asset_url (str): URL to download the asset from.
            operational (bool): Whether to submit as OPERATIONAL state.
        """
        ui = config.ui
        submission = cls(name, asset_path, asset_url, operational)
        submission.validate_inputs()

        with ui.interactive():
            ui.text = "Preparing asset"
            submission.prepare_asset()
            submission.create_asset_object()
            submission.validate_asset_file()
            ui.text = "Submitting asset to MedPerf"
            updated_body = submission.upload()
            submission.to_permanent_path(updated_body)
            submission.write(updated_body)

        ui.print(f"Asset registered with UID: {submission.asset.id}")
        return submission.asset.id

    def __init__(self, name, asset_path, asset_url, operational):
        self.name = name
        self.asset_path = sanitize_path(asset_path)
        self.asset_url = asset_url
        self.operational = operational
        self.asset = None
        self.asset_hash = None

    def validate_inputs(self):
        if not self.asset_path and not self.asset_url:
            raise InvalidArgumentError(
                "Either asset path or asset URL must be provided."
            )
        if self.asset_path and self.asset_url:
            raise InvalidArgumentError(
                "Only one of asset path or asset URL should be provided."
            )
        if self.asset_path:
            if not os.path.exists(self.asset_path):
                raise InvalidArgumentError(
                    f"Asset path does not exist: {self.asset_path}"
                )
            if not os.path.isfile(self.asset_path):
                raise InvalidArgumentError(
                    f"Asset path is not a file: {self.asset_path}"
                )

    def prepare_asset(self):
        if self.asset_path:
            logging.debug("Local asset path provided")
            self.asset_hash = get_file_hash(self.asset_path)
            self.asset_url = "local"
        else:
            self.asset_hash = resources.get_hashed_file(self.asset_url, self.asset_hash)
            logging.debug("Asset URL provided, downloading asset")

    def create_asset_object(self):
        """Creates the Asset entity object with the computed hash and URL."""
        state = "OPERATION" if self.operational else "DEVELOPMENT"
        self.asset = Asset(
            name=self.name,
            asset_hash=self.asset_hash,
            asset_url=self.asset_url,
            state=state,
        )
        os.makedirs(self.asset.path, exist_ok=True)
        config.tmp_paths.append(self.asset.path)
        if self.asset_path:
            self.asset.set_archive_path(self.asset_path)

    def validate_asset_file(self):
        """Makes sure the asset file is a valid archive that can be extracted."""
        self.asset.prepare_asset_files()

    def upload(self):
        updated_body = self.asset.upload()
        return updated_body

    def to_permanent_path(self, asset_dict):
        old_asset_loc = self.asset.path
        updated_asset = Asset(**asset_dict)
        new_asset_loc = updated_asset.path
        remove_path(new_asset_loc)
        os.rename(old_asset_loc, new_asset_loc)

    def write(self, updated_body):
        self.asset = Asset(**updated_body)
        self.asset.write()
