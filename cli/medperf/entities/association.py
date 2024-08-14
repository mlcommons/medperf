from datetime import datetime
from typing import Optional

from medperf.entities.schemas import ApprovableSchema, MedperfBaseSchema


class Association(MedperfBaseSchema, ApprovableSchema):
    id: int
    metadata: dict
    dataset: Optional[int]
    model_mlcube: Optional[int]
    benchmark: int
    initiated_by: int
    created_at: Optional[datetime]
    modified_at: Optional[datetime]
