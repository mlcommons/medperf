from datetime import datetime
from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Optional, Union

from medperf.enums import Status


class MedperfSchema(BaseModel):
    id: Optional[Union[str, int]]
    name: str = Field(..., max_length=20)
    owner: Optional[int]
    created_at: Optional[datetime]
    modified_at: Optional[datetime]
    # TODO: This must change after allowing edits
    state: str = "OPERATION"
    is_valid: bool = True

    def dict(self, *args, **kwargs) -> dict:
        """Overrides dictionary implementation so it filters out
        fields not defined in the pydantic model

        Returns:
            dict: filtered dictionary
        """
        fields = self.__fields__
        valid_fields = []
        # Gather all the field names, both original an alias names
        for field_name, field_item in fields.items():
            valid_fields.append(field_name)
            valid_fields.append(field_item.alias)
        # Remove duplicates
        valid_fields = set(valid_fields)
        model_dict = super().dict(*args, **kwargs)
        out_dict = {k: v for k, v in model_dict.items() if k in valid_fields}
        return out_dict

    def extended_dict(self) -> dict:
        """Dictionary containing both original and alias fields

        Returns:
            dict: Extended dictionary representation
        """
        og_dict = self.dict()
        alias_dict = self.dict(by_alias=True)
        og_dict.update(alias_dict)
        for k, v in og_dict.items():
            if v is None:
                og_dict[k] = ""
            if isinstance(v, HttpUrl):
                og_dict[k] = str(v)
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


class ApprovableSchema(MedperfSchema):
    approved_at: Optional[datetime]
    approval_status: Status = None

    @validator("approval_status", pre=True, always=True)
    def default_status(cls, v):
        status = Status.PENDING
        if v is not None:
            status = Status(v)
        return status


class ResultModel(ApprovableSchema):
    benchmark: int
    model: int
    dataset: int
    results: dict
    metadata: dict = {}
