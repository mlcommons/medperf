from typing import Optional, Union
from medperf.enums import Status
from medperf.entities.dataset import Dataset


class TestDataset(Dataset):
    id: Optional[int] = 1
    name: str = "name"
    location: str = "location"
    data_preparation_mlcube: Union[int, str] = 1
    input_data_hash: str = "input_data_hash"
    generated_uid: str = "generated_uid"
    generated_metadata: dict = {}
    status: Status = Status.APPROVED.value
    state: str = "PRODUCTION"
