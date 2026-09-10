"""Telling a workload identity pool how to read an attestation."""

import logging

from googleapiclient.discovery import build


def update_oidc_provider(
    provider_name: str, attribute_mapping: dict, attribute_condition: str
):
    iam = build("iam", "v1")

    body = {
        "attributeMapping": attribute_mapping,
        "attributeCondition": attribute_condition,
    }
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
    logging.debug(f"Updated OIDC provider {provider_name}")
