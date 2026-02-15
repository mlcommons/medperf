import os

import medperf.config as config
from medperf.entities.model import Model
from medperf.entities.cube import Cube
from medperf.entities.asset import Asset
from medperf.exceptions import InvalidArgumentError
from medperf.utils import remove_path
from medperf.enums import ModelType


class SubmitModel:
    @classmethod
    def run(
        cls,
        name: str,
        container_id: int = None,
        asset_id: int = None,
        operational: bool = False,
    ):
        """Submits a new model to the medperf platform.

        A model wraps either a container or a file-based asset.

        Args:
            name (str): Name of the model.
            container_id (int): ID of the registered container (for CONTAINER type).
            asset_id (int): ID of the registered asset (for ASSET type).
            operational (bool): Whether to submit as OPERATIONAL state.
        """
        ui = config.ui
        submission = cls(name, container_id, asset_id, operational)
        submission.validate_inputs()

        with ui.interactive():
            ui.text = "Submitting model to MedPerf"
            submission.create_model_object()
            updated_body = submission.upload()
            submission.to_permanent_path(updated_body)
            submission.write(updated_body)

        ui.print(f"Model registered with UID: {submission.model.id}")
        return submission.model.id

    def __init__(self, name, container_id, asset_id, operational):
        self.name = name
        self.container_id = container_id
        self.asset_id = asset_id
        self.operational = operational
        self.model = None

    def validate_inputs(self):
        if self.container_id and self.asset_id:
            raise InvalidArgumentError(
                "Container ID and Asset ID cannot both be provided. Please provide only one."
            )
        if not self.container_id and not self.asset_id:
            raise InvalidArgumentError(
                "Either Container ID or Asset ID must be provided. Please provide one."
            )
        if self.container_id:
            Cube.get(self.container_id)  # Validate container exists
        if self.asset_id:
            Asset.get(self.asset_id)  # Validate asset exists

    def create_model_object(self):
        state = "OPERATION" if self.operational else "DEVELOPMENT"
        model_type = (
            ModelType.CONTAINER.value if self.container_id else ModelType.ASSET.value
        )
        self.model = Model(
            name=self.name,
            type=model_type,
            container=self.container_id,
            asset=self.asset_id,
            state=state,
        )
        config.tmp_paths.append(self.model.path)
        os.makedirs(self.model.path, exist_ok=True)

    def upload(self):
        updated_body = self.model.upload()
        return updated_body

    def to_permanent_path(self, model_dict):
        old_path = self.model.path
        updated_model = Model(**model_dict)
        new_path = updated_model.path
        remove_path(new_path)
        os.rename(old_path, new_path)

    def write(self, updated_body):
        self.model = Model(**updated_body)
        self.model.write()
