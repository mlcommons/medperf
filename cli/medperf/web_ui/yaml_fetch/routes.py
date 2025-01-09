import os.path
from enum import Enum
from fastapi import APIRouter, HTTPException, Depends
from medperf.entities.cube import Cube
import requests
import yaml

from medperf.entities.dataset import Dataset
from medperf.web_ui.common import get_current_user_api

router = APIRouter()


class FieldsToFetch(Enum):
    mlcube_yaml = "git_mlcube_url"
    param_yaml = "git_parameters_url"
    dataset_report_path = "report_path"
    dataset_statistics_path = "statistics_path"


class EntityToFetch(Enum):
    mlcube = "mlcube"
    dataset = "dataset"


@router.get("/fetch-yaml")
def fetch_yaml(
    entity: EntityToFetch,
    entity_uid: int,
    field_to_fetch: FieldsToFetch,
    current_user: bool = Depends(get_current_user_api),
):
    try:
        entity_class = {
            EntityToFetch.mlcube: Cube,
            EntityToFetch.dataset: Dataset,
        }[entity]

        mlcube = entity_class.get(entity_uid)
        yaml_uri = getattr(mlcube, field_to_fetch.value)
        if yaml_uri.startswith("http"):
            # some URL
            response = requests.get(yaml_uri)
            response.raise_for_status()  # Check if the request was successful
            content = response.text
        elif os.path.exists(yaml_uri):
            # local file
            with open(yaml_uri, "r") as file:
                content = file.read()
        else:
            raise HTTPException(status_code=400, detail=f"Invalid YAML URL: {yaml_uri}")
        # Validate YAML content
        try:
            yaml.safe_load(content)
        except yaml.YAMLError:
            raise HTTPException(status_code=400, detail="Invalid YAML content")

        return {"content": content}
    except requests.RequestException:
        raise HTTPException(status_code=400, detail="Failed to fetch YAML content")
