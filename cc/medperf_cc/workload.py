"""The environment a confidential workload reads when it starts.

The `EXPECTED_*` values are what a key release backend matches an attestation
against, so they are exactly the terms a workload's identity is built from.
Nothing else belongs here: a value the workload does not need, or that no
backend checks, only widens the attested surface.
"""

import json
from typing import Dict

from medperf_cc.identity import WorkloadIdentity


def workload_env(
    workload: WorkloadIdentity,
    data_config: dict,
    model_config: dict,
    result_config: dict,
    result_collector_public_key: str,
) -> Dict[str, str]:
    return {
        "DATA_CONFIG": json.dumps(data_config),
        "MODEL_CONFIG": json.dumps(model_config),
        "RESULT_CONFIG": json.dumps(result_config),
        "RESULT_COLLECTOR": result_collector_public_key,
        "EXPECTED_DATA_HASH": workload.data_hash,
        "EXPECTED_MODEL_HASH": workload.model_hash,
        "EXPECTED_RESULT_COLLECTOR_HASH": workload.result_collector_hash,
    }
