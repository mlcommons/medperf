from .token_storage import TokenStore
from medperf.config_management import config
from medperf import settings
from medperf.exceptions import MedperfException


def read_user_account():
    config_p = config.read_config()
    if settings.credentials_keyword not in config_p.active_profile:
        return

    account_info = config_p.active_profile[settings.credentials_keyword]
    return account_info


def set_credentials(
    access_token,
    refresh_token,
    id_token_payload,
    token_issued_at,
    token_expires_in,
    login_event=False,
):
    email = id_token_payload["email"]
    TokenStore().set_tokens(email, access_token, refresh_token)
    config_p = config.read_config()

    if login_event:
        # Set the time the user logged in, so that we can track the lifetime of
        # the refresh token
        logged_in_at = token_issued_at
    else:
        # This means this is a refresh event. Preserve the logged_in_at timestamp.
        logged_in_at = config_p.active_profile[settings.credentials_keyword][
            "logged_in_at"
        ]

    account_info = {
        "email": email,
        "token_issued_at": token_issued_at,
        "token_expires_in": token_expires_in,
        "logged_in_at": logged_in_at,
    }

    config_p.active_profile[settings.credentials_keyword] = account_info
    config_p.write_config()


def read_credentials():
    account_info = read_user_account()
    if account_info is None:
        raise MedperfException("You are not logged in")
    email = account_info["email"]
    access_token, refresh_token = TokenStore().read_tokens(email)

    return {
        **account_info,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


def delete_credentials():
    config_p = config.read_config()
    if settings.credentials_keyword not in config_p.active_profile:
        raise MedperfException("You are not logged in")

    email = config_p.active_profile[settings.credentials_keyword]["email"]
    TokenStore().delete_tokens(email)

    config_p.active_profile.pop(settings.credentials_keyword)
    config_p.write_config()


def set_medperf_user_data():
    """Get and cache user data from the MedPerf server"""
    config_p = config.read_config()
    medperf_user = config.comms.get_current_user()

    config_p.active_profile[settings.credentials_keyword]["medperf_user"] = medperf_user
    config_p.write_config()

    return medperf_user


def get_medperf_user_data():
    """Return cached medperf user data. Get from the server if not found"""
    config_p = config.read_config()
    if settings.credentials_keyword not in config_p.active_profile:
        raise MedperfException("You are not logged in")

    medperf_user = config_p.active_profile[settings.credentials_keyword].get(
        "medperf_user", None
    )
    if medperf_user is None:
        medperf_user = set_medperf_user_data()

    return medperf_user
