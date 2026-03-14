import logging
from .types import GCPAssetConfig
from googleapiclient.discovery import build


def update_workload_identity_pool_oidc_provider(
    config: GCPAssetConfig, attribute_mapping: dict, attribute_condition: str
):
    # Authenticate
    iam = build("iam", "v1")

    # Construct the full provider name
    provider_name = config.full_wip_provider_name

    body = {
        "attributeMapping": attribute_mapping,
        "attributeCondition": attribute_condition,
    }

    # Update the OIDC provider
    try:
        request = (
            iam.projects()
            .locations()
            .workloadIdentityPools()
            .providers()
            .patch(
                name=provider_name,
                updateMask="attributeMapping,attributeCondition",
                body=body,
            )
        )
        request.execute()
    except Exception as e:
        logging.debug(f"Failed to update OIDC provider {provider_name}: {e}")
        raise
    logging.debug(
        f"Updated OIDC provider for workload identity pool {config.wip} "
        f"with new attribute mapping and condition."
    )
