from datetime import datetime
from pydantic import BaseModel, HttpUrl, Field, validator
from typing import List, Optional, Union

from medperf.enums import Status


class MedPerfModel(BaseModel):
    id: Optional[Union[int, str]]
    name: str = Field(..., max_length=20)
    owner: Optional[int]
    created_at: Optional[datetime]
    modified_at: Optional[datetime]
    state: str = "DEVELOPMENT"
    is_valid: bool = True

    def extended_dict(self) -> dict:
        """Dictionary containing both original and alias fields

        Returns:
            dict: Extended dictionary representation
        """
        og_dict = self.dict()
        alias_dict = self.dict(by_alias=True)
        og_dict.update(alias_dict)
        return og_dict

    @validator("*", pre=True)
    def empty_str_to_none(cls, v):
        print(v)
        if v == "":
            return None
        return v


class ApprovableModel(MedPerfModel):
    approved_at: Optional[datetime]
    approval_status: Status = None

    @validator("approval_status", pre=True, always=True)
    def default_status(cls, v):
        return Status(v) or Status.PENDING


class BenchmarkModel(ApprovableModel):
    description: Optional[str] = Field(None, max_length=20)
    docs_url: Optional[HttpUrl]
    demo_dataset_tarball_url: Optional[HttpUrl]
    demo_dataset_tarball_hash: str
    demo_dataset_generated_uid: Optional[str]
    data_preparation_mlcube: int
    reference_model_mlcube: int
    data_evaluator_mlcube: int
    models: List[int]
    metadata: dict = {}
    user_metadata: dict = {}
    is_active: bool = True


class CubeModel(MedPerfModel):
    git_mlcube_url: HttpUrl
    mlcube_hash: str
    git_parameters_url: HttpUrl
    parameters_hash: str
    image_tarball_url: HttpUrl
    image_tarball_hash: str
    additional_files_tarball_url: HttpUrl = Field(..., alias="tarball_url")
    additional_files_tarball_hash: str = Field(..., alias="tarball_hash")
    metadata: dict = {}
    user_metadata: dict = {}


class DatasetModel(MedPerfModel):
    description: Optional[str] = Field(None, max_length=20)
    location: str = Field(..., max_length=20)
    data_preparation_mlcube: int
    input_data_hash: str
    generated_uid: str
    split_seed: Optional[int]
    generated_metadata: dict = Field(..., alias="metadata")
    status: Status = None
    separate_labels: Optional[bool]
    user_metadata: dict = {}

    @validator("status", pre=True, always=True)
    def default_status(cls, v, *, values, **kwargs):
        default = Status.PENDING
        if values["id"] is not None:
            default = Status.APPROVED
        return Status(v) or default


class ResultModel(ApprovableModel):
    benchmark: int
    model: int
    dataset: int
    results: dict
    metadata: dict = {}
