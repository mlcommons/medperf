import requests
import json
import argparse


def token_from_online_storage(email):
    """Gets tokens stored in a google cloud bucket."""
    url = "https://storage.googleapis.com/medperf-storage/mock_users_tokens.json"
    res = requests.get(url)
    if res.status_code != 200:
        raise RuntimeError(
            "Could not get token from online bucket: error: "
            + str(res.status_code)
            + " : "
            + res.text
        )
    content = res.text
    try:
        json.loads(content)[email]
    except json.JSONDecodeError:
        raise RuntimeError("Invalid URL")
    except KeyError:
        raise RuntimeError("Invalid email")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--email")

    args = parser.parse_args()
    access_token = token_from_online_storage(args.email)
    print(access_token)
