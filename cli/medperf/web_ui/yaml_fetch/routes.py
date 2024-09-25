from fastapi import APIRouter, HTTPException
import requests
import yaml

router = APIRouter()


@router.get("/fetch-yaml")
async def fetch_yaml(url: str):  # url == https://some-external-malicious-server.com/tracking_url
    # or file:///~/.ssh/id_rsa
    # or http://local-sharepoint.local/secret.yaml
    # solution: pass mlcube_id + name of field to fetch
    try:
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
