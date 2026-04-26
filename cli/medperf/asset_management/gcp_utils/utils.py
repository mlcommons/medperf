import google.auth


def get_user_credentials():
    creds, _ = google.auth.default()
    return creds
