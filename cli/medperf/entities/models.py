from datetime import datetime
from pydantic import BaseModel, HttpUrl, Field, validator
from typing import List, Optional, Union

from medperf.enums import Status


class MedPerfModel(BaseModel):
    @validator("*", pre=True)
    def empty_str_to_none(cls, v):
        print(v)
        if v == "":
            return None
        return v


class BenchmarkModel(MedPerfModel):
    id: Optional[Union[int, str]]
    name: str = Field(..., max_length=20)
    description: str = Field(..., max_length=20)
    docs_url: Optional[HttpUrl]
    created_at: Optional[datetime]
    modified_at: Optional[datetime]
    approved_at: Optional[datetime]
    owner: Optional[int]
    demo_dataset_tarball_url: HttpUrl
    demo_dataset_tarball_hash: str
    demo_dataset_generated_uid: Optional[str]
    data_preparation_mlcube: int
    reference_model_mlcube: int
    data_evaluator_mlcube: int
    models: List[int]
    state: str = "DEVELOPMENT"
    is_valid: bool = True
    is_active: bool = True
    approval_status: Status = Status.PENDING
    metadata: dict = {}
    user_metadata: dict = {}
