import requests
import argparse
import os


def token_from_credentials(email):
    """Retrieve access tokens using the Resource Owner Flow"""

    # load password from the environment
    try:
        password = os.environ["MOCK_USERS_PASSWORD"]
    except KeyError:
        raise RuntimeError(
            "The environment variable `MOCK_USERS_PASSWORD` must be set."
        )

    auth_domain = "dev-5xl8y6uuc2hig2ly.us.auth0.com"
    audience = "https://localhost-dev/"
    client_id = "PSe6pJzYJ9ZmLuLPagHEDh6W44fv9nat"

    url = f"https://{auth_domain}/oauth/token"
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
        raise RuntimeError(
            "Response code is " + str(res.status_code) + " : " + res.text
        )
    return res.json()["access_token"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--email")

    args = parser.parse_args()
    access_token = token_from_credentials(args.email)
    print(access_token)
