from datetime import datetime
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    HttpUrl,
    ValidationError,
    ConfigDict,
    ValidationInfo,
)
from pydantic_core import PydanticUndefined
from typing import Optional
from collections import defaultdict

from medperf.enums import Status
from medperf.exceptions import MedperfException
from medperf.utils import format_errors_dict


class MedperfSchema(BaseModel):
    for_test: bool = False
    id: Optional[int] = None
    name: str = Field(..., max_length=128, validate_default=True)
    owner: Optional[int] = None
    is_valid: bool = True
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None

    def __init__(self, *args, **kwargs):
        """Override the ValidationError procedure so we can
        format the error message in our desired way
        """
        try:
            super().__init__(*args, **kwargs)
        except ValidationError as e:
            errors_dict = defaultdict(list)
            for error in e.errors():
                field = error["loc"]
                msg = error["msg"]
                errors_dict[field].append(msg)

            error_msg = "Field Validation Error:"
            error_msg += format_errors_dict(errors_dict)

            raise MedperfException(error_msg)

    def dict(self, *args, **kwargs) -> dict:
        """Overrides dictionary implementation so it filters out
        fields not defined in the pydantic model

        Returns:
            dict: filtered dictionary
        """
        fields = self.__class__.model_fields
        valid_fields = []
        # Gather all the field names, both original an alias names
        for field_name, field_item in fields.items():
            valid_fields.append(field_name)
            valid_fields.append(field_item.alias)
        # Remove duplicates
        valid_fields = set(valid_fields)
        model_dict = super().model_dump(*args, **kwargs)
        out_dict = {k: v for k, v in model_dict.items() if k in valid_fields}
        return out_dict

    def model_dump(self, *args, **kwargs) -> dict:
        """
        Added method to have a similar API to Pydantic V2, which recommends using
        .model_dump instead of .dict
        """
        return self.dict(*args, **kwargs)

    def todict(self) -> dict:
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

    @field_validator("*", mode="before")
    @classmethod
    def empty_str_to_none(cls, v, info: ValidationInfo):
        if v == "":
            current_attribute = cls.model_fields[info.field_name]
            default_value = None
            if current_attribute.default != PydanticUndefined:
                default_value = current_attribute.default
            elif current_attribute.default_factory is not None:
                default_value = current_attribute.default_factory()
            return default_value

        return v

    model_config = ConfigDict(
        populate_by_name=True, use_enum_values=True, extra="allow"
    )


class DeployableSchema(BaseModel):
    state: str = "DEVELOPMENT"


class ApprovableSchema(BaseModel):
    approved_at: Optional[datetime] = None
    approval_status: Status = Field(None, validate_default=True)

    @field_validator("approval_status", mode="before")
    def default_status(cls, v):
        status = Status.PENDING
        if v is not None:
            status = Status(v)
        return status
