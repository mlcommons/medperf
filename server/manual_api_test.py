from seed_utils import Server
import json
import argparse
from pathlib import Path

REPO_BASE_DIR = Path(__file__).resolve().parent.parent


def do_test(args):
    api_server = Server(host=args.server, cert=args.cert)
    if args.version:
        api_server.validate(True, args.version)
    else:
        api_server.validate(False)

    tokens = json.load(open(args.tokens))
    get_token = lambda email: tokens[email]  # noqa
    # set admin
    token = get_token("testbo@example.com")
    res = api_server.request(
        "/mlcubes/3/model/",
        "GET",
        token,
        {},
        return_full_response=True,
    )
    print(res)


if __name__ == "__main__":
    default_cert_file = str(REPO_BASE_DIR / "server" / "cert.crt")
    default_tokens_file = str(REPO_BASE_DIR / "mock_tokens" / "tokens.json")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--server",
        type=str,
        help="Server host address to connect",
        default="https://127.0.0.1:8000",
    )
    parser.add_argument(
        "--cert", type=str, help="Server certificate", default=default_cert_file
    )
    parser.add_argument("--version", type=str, help="Server version")
    parser.add_argument(
        "--tokens",
        type=str,
        help="Path to local tokens file",
        default=default_tokens_file,
    )
    args = parser.parse_args()
    if args.cert.lower() == "none":
        args.cert = None
    do_test(args)
