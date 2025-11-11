from medperf.exceptions import MedperfException
from medperf.entities.encrypted_container_key import EncryptedKey
from medperf.entities.cube import Cube
from medperf.account_management import get_medperf_user_data
import logging


def check_access_to_container(container_id: int):
    """
    Check if the current user can access the given container.

    Returns:
        dict: {
            "has_access": bool,
            "reason": str
        }
    """
    container = Cube.get(container_id)
    container.download_config_files()
    if not container.is_encrypted():
        return_dict = {"has_access": True, "reason": "The container is public"}
        logging.debug(f"User access to container: {return_dict}")
        return return_dict

    user_id = get_medperf_user_data()["id"]
    if container.owner == user_id:
        return_dict = {"has_access": True, "reason": "You own the container"}
    else:
        try:
            EncryptedKey.get_user_container_key(container_id)
            return_dict = {"has_access": True, "reason": "Access has been granted"}
        except MedperfException as e:
            return_dict = {"has_access": False, "reason": str(e)}
    logging.debug(f"User access to container: {return_dict}")
    return return_dict
