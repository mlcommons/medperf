from datetime import datetime
from pydantic import BaseModel, Field, validator, HttpUrl, ValidationError
from typing import Optional
from collections import defaultdict

from medperf.enums import Status
from medperf.exceptions import MedperfException


class FormattedBaseModel(BaseModel):
    """Override the ValidationError procedure so we can
    format the error message in our desired way
    """

    def __init__(self, *args, **kwargs):
        try:
            super().__init__(*args, **kwargs)
        except ValidationError as e:
            errors_dict = defaultdict(list)
            for error in e.errors():
                field = error["loc"]
                msg = error["msg"]
                errors_dict[field].append(msg)

            error_msg = "Field Validation Error:"
            for field, errors in errors_dict.items():
                error_msg += "\n"
                field = field[0]
                error_msg += f"- {field}: "
                if len(errors) == 1:
                    # If a single error for a field is given, don't create a sublist
                    error_msg += errors[0]
                else:
                    # Create a sublist otherwise
                    for e_msg in errors:
                        error_msg += "\n"
                        error_msg += f"\t- {e_msg}"

            raise MedperfException(error_msg)


class MedperfSchema(FormattedBaseModel):
    id: Optional[int]
    name: str = Field(..., max_length=20)
    owner: Optional[int]
    created_at: Optional[datetime]
    modified_at: Optional[datetime]

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


class DeployableSchema(FormattedBaseModel):
    # TODO: This must change after allowing edits
    state: str = "OPERATION"
    is_valid: bool = True


class ApprovableSchema(FormattedBaseModel):
    approved_at: Optional[datetime]
    approval_status: Status = None

    @validator("approval_status", pre=True, always=True)
    def default_status(cls, v):
        status = Status.PENDING
        if v is not None:
            status = Status(v)
        return status
