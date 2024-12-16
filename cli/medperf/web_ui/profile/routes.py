import logging

from fastapi import APIRouter, Form

from medperf import settings
from medperf.exceptions import InvalidArgumentError
from medperf.config_management import config

router = APIRouter()


def activate_profile(profile: str) -> None:
    config.read_config()
    if profile not in config:
        raise InvalidArgumentError("The provided profile does not exists")
    config.activate(profile)
    config.write_config()

    logging.debug("new profile activated")
    logging.debug(f"new config creds: {config.active_profile[settings.credentials_keyword]}")


@router.post("/change-profile")
async def change_profile(profile: str = Form(...)):
    activate_profile(profile)
    return {"message": "Profile changed"}
