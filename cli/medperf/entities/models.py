from datetime import datetime
from pydantic import BaseModel, HttpUrl, Field, validator
from typing import List, Optional, Union

from medperf.enums import Status


class MedPerfModel(BaseModel):
    id: Optional[Union[str, int]]
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
        if v == "":
            return None
        return v

    class Config:
        allow_population_by_field_name = True
        extra = "allow"
        use_enum_values = True


class ApprovableModel(MedPerfModel):
    approved_at: Optional[datetime]
    approval_status: Status = None

    @validator("approval_status", pre=True, always=True)
    def default_status(cls, v):
        status = Status.PENDING
        if v is not None:
            status = Status(v)
        return status


class ResultModel(ApprovableModel):
    benchmark: int
    model: int
    dataset: int
    results: dict
    metadata: dict = {}
