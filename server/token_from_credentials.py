import requests
import argparse


def token_from_credentials(email, password, env):
    """Retrieve access tokens using the Resource Owner Flow"""
    if env == "dev":
        auth_domain = "dev-5xl8y6uuc2hig2ly.us.auth0.com"
        audience = "https://localhost-dev/"
        client_id = "PSe6pJzYJ9ZmLuLPagHEDh6W44fv9nat"

    else:
        auth_domain = "mlc-medperf.us.auth0.com"
        audience = "https://localhost-tutorials/"
        client_id = "yOabw1jHnGRfcWTDDyQyzkBbPUinhpsr"

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
    parser.add_argument("--password")
    parser.add_argument("--env", choices=["dev", "tutorial"])

    args = parser.parse_args()
    access_token = token_from_credentials(args.email, args.password, args.env)
    print(access_token)
