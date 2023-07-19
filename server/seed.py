"""Seed the server database with demo entries for integration tests. For simplicity,
Tokens used for mock users are retrieved by password-grant authorization flow.
This script can only be invoked from its parent folder, that's because is
executes Django code to set admin permissions for a test user."""

import argparse
from seed_utils import Server, set_user_as_admin, create_benchmark, create_model
from token_from_credentials import token_from_credentials
from pathlib import Path


def seed(args):
    api_server = Server(host=args.server, cert=args.cert)
    if args.version:
        api_server.validate(True, args.version)
    else:
        api_server.validate(False)

    # get tokens
    admin_token = token_from_credentials("testadmin@example.com")
    benchmark_owner_token = token_from_credentials("testbo@example.com")
    model_owner_token = token_from_credentials("testmo@example.com")

    # set admin
    set_user_as_admin(api_server, admin_token)
    # create benchmark
    benchmark = create_benchmark(api_server, benchmark_owner_token, admin_token)
    # create model
    create_model(api_server, model_owner_token, benchmark_owner_token, benchmark)


if __name__ == "__main__":
    default_cert_file = str(Path(__file__).resolve().parent / "cert.crt")
    parser = argparse.ArgumentParser(description="Seed the db with demo entries")
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
    args = parser.parse_args()
    if args.cert.lower() == "none":
        args.cert = None
    seed(args)
