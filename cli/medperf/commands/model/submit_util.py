import os
from typing import TYPE_CHECKING

import medperf.config as config
from medperf.entities.model import Model
from medperf.utils import remove_path
from medperf.enums import ModelType

if TYPE_CHECKING:
    from medperf.commands.mlcube.submit import SubmitCube
    from medperf.commands.asset.submit import SubmitAsset


class ContinueCubeSubmission:
    @classmethod
    def run(cls, container_submission: "SubmitCube"):
        """Finalizes the container submission.

        Args:
            container_submission (SubmitCube): The submission object for the cube.
        """
        submission = cls(container_submission)
        submission.create_model_object()
        updated_body, container_body = submission.upload()
        submission.finalize_container_submission(container_body)
        submission.to_permanent_path(updated_body)
        submission.write(updated_body)
        return submission.model.container.id

    def __init__(self, container_submission: "SubmitCube"):
        self.container_submission = container_submission
        self.model = None

    def create_model_object(self):
        self.model = Model(
            name=self.container_submission.cube.name,
            type=ModelType.CONTAINER.value,
            container=self.container_submission.cube,
            state=self.container_submission.cube.state,
        )
        config.tmp_paths.append(self.model.path)
        os.makedirs(self.model.path, exist_ok=True)

    def upload(self):
        updated_body = self.model.upload()
        return updated_body, updated_body["container"]

    def finalize_container_submission(self, updated_body: dict):
        self.container_submission.to_permanent_path(updated_body)
        self.container_submission.write(updated_body)
        self.container_submission.store_decryption_key()

    def to_permanent_path(self, model_dict):
        old_path = self.model.path
        updated_model = Model(**model_dict)
        new_path = updated_model.path
        remove_path(new_path)
        os.rename(old_path, new_path)

    def write(self, updated_body):
        self.model = Model(**updated_body)
        self.model.write()


class ContinueAssetSubmission:
    @classmethod
    def run(cls, asset_submission: "SubmitAsset"):
        """Finalizes the asset submission.

        Args:
            asset_submission (SubmitAsset): The submission object for the asset.
        """
        submission = cls(asset_submission)
        submission.create_model_object()
        updated_body, asset_body = submission.upload()
        submission.finalize_asset_submission(asset_body)
        submission.to_permanent_path(updated_body)
        submission.write(updated_body)
        return submission.model.asset.id

    def __init__(self, asset_submission: "SubmitAsset"):
        self.asset_submission = asset_submission
        self.model = None

    def create_model_object(self):
        self.model = Model(
            name=self.asset_submission.asset.name,
            type=ModelType.ASSET.value,
            asset=self.asset_submission.asset,
            state=self.asset_submission.asset.state,
        )
        config.tmp_paths.append(self.model.path)
        os.makedirs(self.model.path, exist_ok=True)

    def upload(self):
        updated_body = self.model.upload()
        return updated_body, updated_body["asset"]

    def finalize_asset_submission(self, updated_body: dict):
        self.asset_submission.to_permanent_path(updated_body)
        self.asset_submission.write(updated_body)

    def to_permanent_path(self, model_dict):
        old_path = self.model.path
        updated_model = Model(**model_dict)
        new_path = updated_model.path
        remove_path(new_path)
        os.rename(old_path, new_path)

    def write(self, updated_body):
        self.model = Model(**updated_body)
        self.model.write()
