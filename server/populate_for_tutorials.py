"""Seed the server database with demo entries for tutorials. Tokens used for
mock users are retrieved from an online storage"""

import argparse
from seed_utils import Server, set_user_as_admin, create_benchmark, create_model
from token_from_online_storage import token_from_online_storage
from pathlib import Path


def seed(args):
    api_server = Server(host=args.server, cert=args.cert)
    api_server.validate(False)

    # get tokens
    admin_token = token_from_online_storage("testadmin@example.com")
    benchmark_owner_token = token_from_online_storage("testbo@example.com")
    model_owner_token = token_from_online_storage("testmo@example.com")

    set_user_as_admin(api_server, admin_token)
    if args.demo == "benchmark":
        return
    benchmark = create_benchmark(api_server, benchmark_owner_token, admin_token)
    if args.demo == "model":
        return
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
    parser.add_argument(
        "--demo",
        type=str,
        help="Populate for a tutorial: 'benchmark', 'model', or 'data'.",
        choices=["benchmark", "model", "data"],
    )
    args = parser.parse_args()
    if args.cert.lower() == "none":
        args.cert = None
    seed(args)
