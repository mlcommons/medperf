# modes

## in dev mode

container_config + set the MEDPERF_ON_PREM env var

## in production mode

DATA_CONFIG
{
    "project_id": "gcp_project_id",
    "project_number": "gcp_project_number",
    "account": "gcp_account",

    "bucket": "gcp_bucket",
    "encrypted_asset_bucket_file": "gcp_encrypted_asset_bucket_file",
    "encrypted_key_bucket_file": "gcp_encrypted_key_bucket_file",

    "keyring_name": "gcp_keyring_name",
    "key_name": "gcp_key_name",
    "wip": "gcp_wip"
}

MODEL_CONFIG same as data config
RESULT_CONFIG
    bucket_name: name of the bucket
    output_result_path: path in the bucket
    results_encryption_key_path: path in the bucket
RESULT_COLLECTOR (string: b64encoded public key of the reciever)

EXPECTED_DATA_HASH (string: hash of the data folders)
EXPECTED_MODEL_HASH (string: hash of the model tar file)
EXPECTED_RESULT_COLLECTOR_HASH (string: hash of b64encoded public key of the reciever)

    --attribute-condition="assertion.swname == 'CONFIDENTIAL_SPACE' \
        && 'STABLE' in assertion.submods.confidential_space.support_attributes"

use no debug image
