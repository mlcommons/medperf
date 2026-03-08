from datetime import datetime
from pydantic import BaseModel, Field, validator
from typing import Optional, Union

from medperf.enums import Status


class MedperfSchema(BaseModel):
    for_test: Optional[bool] = False
    id: Optional[int]
    name: str = Field(..., max_length=128)
    owner: Optional[int]
    is_valid: bool = True
    created_at: Optional[datetime]
    modified_at: Optional[datetime]

    class Config:
        use_enum_values = True


class AggregatorSchema(MedperfSchema):
    metadata: dict = {}
    config: dict
    aggregation_mlcube: int

    @validator("config", pre=True, always=True)
    def check_config(cls, v, *, values, **kwargs):
        keys = set(v.keys())
        allowed_keys = {
            "address",
            "port",
        }
        if keys != allowed_keys:
            raise ValueError("config must contain two keys only: address and port")
        return v


class AssetSchema(MedperfSchema):
    state: str = "DEVELOPMENT"
    asset_hash: str
    asset_url: str
    metadata: dict = {}
    user_metadata: dict = {}


class BenchmarkSchema(MedperfSchema):
    state: str = "DEVELOPMENT"
    approved_at: Optional[datetime]
    approval_status: Status = None
    description: Optional[str] = Field(None, max_length=256)
    docs_url: Optional[str]
    demo_dataset_tarball_url: str
    demo_dataset_tarball_hash: Optional[str]
    demo_dataset_generated_uid: Optional[str]
    data_preparation_mlcube: int
    reference_model: int
    data_evaluator_mlcube: int
    metadata: dict = {}
    user_metadata: dict = {}
    is_active: bool = True
    dataset_auto_approval_allow_list: list[str] = []
    dataset_auto_approval_mode: str = "NEVER"
    model_auto_approval_allow_list: list[str] = []
    model_auto_approval_mode: str = "NEVER"


class CASchema(MedperfSchema):
    metadata: dict = {}
    client_mlcube: int
    server_mlcube: int
    ca_mlcube: int
    config: dict

    @validator("config", pre=True, always=True)
    def check_config(cls, v, *, values, **kwargs):
        keys = set(v.keys())
        allowed_keys = {
            "address",
            "port",
            "fingerprint",
            "client_provisioner",
            "server_provisioner",
        }
        if keys != allowed_keys:
            raise ValueError(
                "CA config must contain these exact 5 keys:\n"
                "address, port, fingerprint, client_provisioner, server_provisioner"
            )
        return v


class CertificateSchema(MedperfSchema):
    certificate_content_base64: str
    ca: int


class CubeSchema(MedperfSchema):
    state: str = "DEVELOPMENT"
    container_config: dict
    parameters_config: Optional[dict]
    image_hash: Optional[str]
    additional_files_tarball_url: Optional[str]
    additional_files_tarball_hash: Optional[str]
    metadata: dict = Field(default_factory=dict)
    user_metadata: dict = Field(default_factory=dict)


class DatasetSchema(MedperfSchema):
    state: str = "DEVELOPMENT"
    description: Optional[str] = Field(None, max_length=256)
    location: Optional[str] = Field(None, max_length=128)
    input_data_hash: str
    generated_uid: str
    data_preparation_mlcube: int
    split_seed: Optional[int]
    generated_metadata: dict
    user_metadata: dict = {}
    report: dict = {}
    submitted_as_prepared: bool


class EncryptedKeySchema(MedperfSchema):
    encrypted_key_base64: str
    container: int
    certificate: int


class TrainingEventSchema(MedperfSchema):
    training_exp: int
    participants: dict
    finished: bool = False
    finished_at: Optional[datetime]
    report: Optional[dict]


class ExecutionSchema(MedperfSchema):
    approved_at: Optional[datetime]
    approval_status: Status = None
    benchmark: int
    model: int
    dataset: int
    results: dict = {}
    metadata: dict = {}
    user_metadata: dict = {}
    model_report: dict = {}
    evaluation_report: dict = {}
    finalized: bool = False
    finalized_at: Optional[datetime]


class ModelSchema(MedperfSchema):
    state: str = "DEVELOPMENT"
    type: str  # ASSET or CONTAINER
    container: Optional[CubeSchema]
    asset: Optional[AssetSchema]
    metadata: dict = {}
    user_metadata: dict = {}


class TestReportSchema(MedperfSchema):
    name: Optional[str] = "name"
    demo_dataset_url: Optional[str]
    demo_dataset_hash: Optional[str]
    prepared_data_hash: Optional[str]
    data_preparation_mlcube: Optional[Union[int, str]]
    model: Union[int, str]
    data_evaluator_mlcube: Union[int, str]
    results: Optional[dict]


class TrainingExpSchema(MedperfSchema):
    approved_at: Optional[datetime]
    approval_status: Status = None
    state: str = "DEVELOPMENT"
    description: Optional[str] = Field(None, max_length=256)
    docs_url: Optional[str]
    demo_dataset_tarball_url: str
    demo_dataset_tarball_hash: Optional[str]
    demo_dataset_generated_uid: Optional[str]
    data_preparation_mlcube: int
    fl_mlcube: int
    fl_admin_mlcube: Optional[int]
    plan: dict = {}
    metadata: dict = {}
    user_metadata: dict = {}


class UserSchema(BaseModel):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    metadata: dict = {}
