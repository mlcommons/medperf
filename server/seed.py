"""Seed the server database with demo entries for integration tests or tutorials.
Tokens to access the local server are either from the local JWT factory provided
in the repository root, or from the auth provider. The later case is to do
integration tests with the auth provider. For simplicity, the auth provider
tokens used for mock users are retrieved by password-grant authorization flow.

This script can only be invoked from its parent folder, that's because it
executes Django code to set admin permissions for a test user."""

import argparse
from seed_utils import (
    Server,
    set_user_as_admin,
    create_benchmark,
    create_model,
    create_workflow_benchmark,
    associate_model_to_benchmark,
    create_benchmark_ref_model_and_metrics_containers,
)
from auth_provider_token import auth_provider_token
from pathlib import Path
import json

REPO_BASE_DIR = Path(__file__).resolve().parent.parent


def populate_mock_benchmarks(api_server, admin_token):
    demo_url = "https://storage.googleapis.com/medperf-storage/chestxray_tutorial/demo_data.tar.gz"
    for name, description in [
        ("Mock Brain Tumors Segmentation", "Mock benchmark for development purposes"),
        ("Mock Skin Cancer Detection", "Mock benchmark for development purposes"),
    ]:
        api_server.request(
            "/benchmarks/",
            "POST",
            admin_token,
            {
                "name": name,
                "description": description,
                "docs_url": "",
                "demo_dataset_tarball_url": demo_url,
                "demo_dataset_tarball_hash": "71faabd59139bee698010a0ae3a69e16d97bc4f2dde799d9e187b94ff9157c00",
                "demo_dataset_generated_uid": "730d2474d8f22340d9da89fa2eb925fcb95683e0",
                "data_preparation_mlcube": 1,
                "reference_model_mlcube": 1,
                "data_evaluator_mlcube": 1,
                "state": "OPERATION",
            },
            "id",
        )


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

    if args.demo == "tutorial":
        populate_mock_benchmarks(api_server, admin_token)
        return

    if args.demo == "benchmark":
        return
    # create benchmark
    benchmark_owner_token = get_token("testbo@example.com")
    ref_model, evaluator = create_benchmark_ref_model_and_metrics_containers(
        api_server, benchmark_owner_token, admin_token
    )
    container_benchmark = create_benchmark(
        api_server, ref_model, evaluator, benchmark_owner_token, admin_token
    )
    workflow_benchmark = create_workflow_benchmark(
        api_server, ref_model, evaluator, benchmark_owner_token, admin_token
    )
    if args.demo == "model":
        return
    # create model
    model_owner_token = get_token("testmo@example.com")
    model = create_model(api_server, model_owner_token)
    associate_model_to_benchmark(
        api_server, model_owner_token, benchmark_owner_token, model, container_benchmark
    )
    associate_model_to_benchmark(
        api_server,
        model_owner_token,
        benchmark_owner_token,
        model,
        workflow_benchmark,
    )


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
        choices=["benchmark", "model", "data", "tutorial"],
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
