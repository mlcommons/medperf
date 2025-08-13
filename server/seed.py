"""Seed the server database with demo entries for integration tests or tutorials.
Tokens to access the local server are either from the local JWT factory provided
in the repository root, or from the auth provider. The later case is to do
integration tests with the auth provider. For simplicity, the auth provider
tokens used for mock users are retrieved by password-grant authorization flow.

This script can only be invoked from its parent folder, that's because it
executes Django code to set admin permissions for a test user."""

import argparse
from seed_utils import Server, set_user_as_admin, create_benchmark, create_model, create_private_model
from auth_provider_token import auth_provider_token
from pathlib import Path
import json

REPO_BASE_DIR = Path(__file__).resolve().parent.parent


def seed(args):
    api_server = Server(host=args.server, cert=args.cert)
    if args.version:
        api_server.validate(True, args.version)
    else:
        api_server.validate(False)

    # setup tokens source
    if args.auth == "local":
        tokens = json.load(open(args.tokens))
        get_token = lambda email: tokens[email]  # noqa
    else:
        get_token = auth_provider_token

    # set admin
    admin_token = get_token("testadmin@example.com")
    set_user_as_admin(api_server, admin_token)
    if args.demo == "benchmark":
        return
    # create benchmark
    benchmark_owner_token = get_token("testbo@example.com")
    benchmark = create_benchmark(api_server, benchmark_owner_token, admin_token)
    if args.demo == "model":
        return
    # create model
    model_owner_token = get_token("testmo@example.com")
    create_model(api_server, model_owner_token, benchmark_owner_token, benchmark)

    # create private model
    private_model_owner_token = get_token("testpo@example.com")
    create_private_model(api_server, private_model_owner_token, benchmark_owner_token, benchmark)

if __name__ == "__main__":
    default_cert_file = str(REPO_BASE_DIR / "server" / "cert.crt")
    default_tokens_file = str(REPO_BASE_DIR / "mock_tokens" / "tokens.json")

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
    parser.add_argument(
        "--auth",
        type=str,
        help="Authentication mode",
        default="local",
        choices=["local", "online"],
    )
    parser.add_argument(
        "--demo",
        type=str,
        help="Seed for a tutorial: 'benchmark', 'model', or 'data'.",
        default="data",
        choices=["benchmark", "model", "data"],
    )
    parser.add_argument(
        "--tokens",
        type=str,
        help="Path to local tokens file",
        default=default_tokens_file,
    )
    args = parser.parse_args()
    if args.cert.lower() == "none":
        args.cert = None
    seed(args)
