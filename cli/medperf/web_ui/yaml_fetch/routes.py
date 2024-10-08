from enum import Enum
from fastapi import APIRouter, HTTPException
from medperf.entities.cube import Cube
import requests
import yaml

router = APIRouter()

class FieldsToFetch(Enum):
   mlcube_yaml = "git_mlcube_url"
   param_yaml = "git_parameters_url"


@router.get("/fetch-yaml")
async def fetch_yaml(mlcube_uid: int, field_to_fetch: FieldsToFetch):
    try:
        mlcube = Cube.get(mlcube_uid)
        url = getattr(mlcube, field_to_fetch.value)
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful
        content = response.text

        # Validate YAML content
        try:
            yaml.safe_load(content)
        except yaml.YAMLError:
            raise HTTPException(status_code=400, detail="Invalid YAML content")

        return {"content": content}
    except requests.RequestException:
        raise HTTPException(status_code=400, detail="Failed to fetch YAML content")
