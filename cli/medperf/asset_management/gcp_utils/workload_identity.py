import logging
from medperf.utils import run_command
from .types import GCPAssetConfig


def update_workload_identity_pool_oidc_provider(
    config: GCPAssetConfig, attribute_mapping: str, attribute_condition: str
):
    cmd = [
        "gcloud",
        "iam",
        "workload-identity-pools",
        "providers",
        "update-oidc",
        config.wip_provider,
        "--location=global",
        f"--workload-identity-pool={config.wip}",
        f"--attribute-mapping={attribute_mapping}",
        f"--attribute-condition={attribute_condition}",
    ]
    run_command(cmd)
    logging.debug(
        f"Updated OIDC provider for workload identity pool {config.wip}"
        f" with new attribute mapping and condition."
    )
