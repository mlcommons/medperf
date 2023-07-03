import os
import sys
import requests
import json
import curlify
import django
from django.contrib.auth import get_user_model


def auth0_token_for_ci(email, password):
    """Retrieve access tokens using the Resource Owner Flow"""
    auth0_domain = "dev-5xl8y6uuc2hig2ly.us.auth0.com"
    audience = "https://localhost-dev/"
    client_id = "PSe6pJzYJ9ZmLuLPagHEDh6W44fv9nat"

    url = f"https://{auth0_domain}/oauth/token"
    headers = {"content-type": "application/x-www-form-urlencoded"}
    body = {
        "client_id": client_id,
        "audience": audience,
        "grant_type": "password",
        "username": email,
        "password": password,
    }
    res = requests.post(url=url, headers=headers, data=body)
    if res.status_code != 200:
        sys.exit(
            "Auth0 Response code is "
            + str(res.status_code)
            + " : "
            + res.text
            + " curl request "
            + curlify.to_curl(res.request)
        )
    return res.json()["access_token"]


def auth0_token_for_tutorials(user_keyword):
    """Gets tokens stored in a google cloud bucket."""
    url = "https://storage.googleapis.com/medperf-storage/mock_users_tokens.json"
    content = requests.get(url).text
    return json.loads(content)[user_keyword]


def set_user_as_admin(api_server, access_token):
    os.environ["DJANGO_SETTINGS_MODULE"] = "medperf.settings"
    django.setup()

    user_id = api_server.request("/me/", "GET", access_token, {}, out_field="id")

    User = get_user_model()
    user = User.objects.get(id=user_id)

    user.is_staff = True
    user.is_superuser = True
    user.save()
