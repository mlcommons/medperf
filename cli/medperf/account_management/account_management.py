from .token_storage import TokenStore
from medperf.config_management import read_config, write_config
from medperf import config
from medperf.exceptions import MedperfException


def read_user_account():
    config_p = read_config()
    if config.credentials_keyword not in config_p.active_profile:
        raise MedperfException("You are not logged in")

    account_info = config_p.active_profile[config.credentials_keyword]
    return account_info


def set_credentials(
    access_token,
    refresh_token,
    id_token_payload,
    token_issued_at,
    token_expires_in,
):
    email = id_token_payload["email"]
    TokenStore().set_tokens(email, access_token, refresh_token)

    account_info = {
        "email": email,
        "token_issued_at": token_issued_at,
        "token_expires_in": token_expires_in,
    }
    config_p = read_config()
    config_p.active_profile[config.credentials_keyword] = account_info
    write_config(config_p)


def read_credentials():
    account_info = read_user_account()
    email = account_info["email"]
    access_token, refresh_token = TokenStore().read_tokens(email)

    return {
        **account_info,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


def delete_credentials():
    config_p = read_config()
    if config.credentials_keyword not in config_p.active_profile:
        raise MedperfException("You are not logged in")

    email = config_p.active_profile[config.credentials_keyword]["email"]
    TokenStore().delete_tokens(email)

    config_p.active_profile.pop(config.credentials_keyword)
    write_config(config_p)


def set_medperf_user_data():
    """Get and cache user data from the MedPerf server"""
    config_p = read_config()
    medperf_user = config.comms.get_current_user()

    config_p.active_profile[config.credentials_keyword]["medperf_user"] = medperf_user
    write_config(config_p)

    return medperf_user


def get_medperf_user_data():
    """Return cached medperf user data. Get from the server if not found"""
    config_p = read_config()
    if config.credentials_keyword not in config_p.active_profile:
        raise MedperfException("You are not logged in")

    medperf_user = config_p.active_profile[config.credentials_keyword].get(
        "medperf_user", None
    )
    if medperf_user is None:
        medperf_user = set_medperf_user_data()

    return medperf_user
