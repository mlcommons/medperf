from enum import Enum
from fastapi import APIRouter, HTTPException, Depends
from medperf.entities.cube import Cube
import requests
import yaml

from medperf.entities.dataset import Dataset
from medperf.web_ui.common import check_user_api

router = APIRouter()


class FieldsToFetch(Enum):
    container_config = "container_config"
    parameters_config = "parameters_config"
    dataset_report_path = "report_path"
    dataset_statistics_path = "statistics_path"


class EntityToFetch(Enum):
    container = "container"
    dataset = "dataset"


@router.get("/fetch-yaml")
def fetch_yaml(
    entity: EntityToFetch,
    entity_uid: int,
    field_to_fetch: FieldsToFetch,
    current_user: bool = Depends(check_user_api),
):
    try:
        entity_class = {
            EntityToFetch.container: Cube,
            EntityToFetch.dataset: Dataset,
        }[entity]

        container = entity_class.get(entity_uid)
        json_content = getattr(container, field_to_fetch.value)
        content = yaml.safe_dump(json_content)
        print(f"{content=}")
        return {"content": content}
    except requests.RequestException:
        raise HTTPException(status_code=400, detail="Failed to fetch YAML content")
