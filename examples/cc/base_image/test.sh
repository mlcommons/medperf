# first, grant KMS permissions to the google cloud project/user to be able to run without CC
DATA_CONFIG='{"project_id": "data-owner-cc", "project_number": "470901555042", "account": "hasankassim8@gmail.com", "bucket": "data-owner-bucket-medperf", "encrypted_asset_bucket_file": "data.enc", "encrypted_key_bucket_file": "key.enc", "keyring_name": "data-owner-keyring", "key_name": "data-owner-key2", "wip": "data-owner-wip"}'
MODEL_CONFIG='{"project_id": "model-owner-cc", "project_number": "280894108292", "account": "hasankassim8@gmail.com", "bucket": "model-owner-bucket", "encrypted_asset_bucket_file": "model.enc", "encrypted_key_bucket_file": "key.enc", "keyring_name": "model-owner-keyring", "key_name": "model-owner-key", "wip": "model-owner-wip"}'
RESULT_CONFIG='{"bucket": "data-owner-bucket-medperf", "encrypted_result_bucket_file": "sha256_e1d3b8f2428c8ef75b68fa0fcd8712d13e35918615da7abe1d43d4ccce8fef20__c98cd5fb0f69280de73056cdc6a5cbd3726f715e5e952406e7418ed0d1a8c738__bff003e244759c3d7c8b9784af0819c7f252da8626745671ccf7f46b8f19a0ca__7f9a26c8e38f2c806f52c99cfe2f90f93963c808f16131b8f8adb07cdd4e7e84/output", "encrypted_key_bucket_file": "sha256_e1d3b8f2428c8ef75b68fa0fcd8712d13e35918615da7abe1d43d4ccce8fef20__c98cd5fb0f69280de73056cdc6a5cbd3726f715e5e952406e7418ed0d1a8c738__bff003e244759c3d7c8b9784af0819c7f252da8626745671ccf7f46b8f19a0ca__7f9a26c8e38f2c806f52c99cfe2f90f93963c808f16131b8f8adb07cdd4e7e84/encryption_key"}'
EXPECTED_DATA_HASH="c98cd5fb0f69280de73056cdc6a5cbd3726f715e5e952406e7418ed0d1a8c738"
EXPECTED_MODEL_HASH="bff003e244759c3d7c8b9784af0819c7f252da8626745671ccf7f46b8f19a0ca"
RESULT_COLLECTOR="LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUlJQm9qQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FZOEFNSUlCaWdLQ0FZRUF6ZEV6M3Y0SlNMVTRNS3NTOWI3OAplZDBCLzh0WER0V2hEMnc3S0lRZkRTa0hiOG1yQnVaZDN2cE5aY3J6ZUpjWjRUNXNFMmZzVnJKRFdsTGJnL0NGCkw2V3o4SEVEelU2VHFua2RVMlY4RVZuS3lGZHJ2SkNUOVE4THR3Mk5QSEJ1YVNuYU9uaS80TUZQTDFuOGc3anAKdk1uNGM2aHlYZndoekhkVlpJaUJQaDc4WngrcWN5cWRVZTk2d2x6MEVSZkhqOWJjZE1sTUZXUVZsZG9pQURxZgpzdlZCUVZFbWRCcGszUG13K0dNcHpIZ3BUNU1sZTdZQXd6ZDc1bmMwTGo1U2pnT2t1VmJMb1dGZFlqV2hNTnptCnVCNWRBVTRHSUtQakY1Tk9aaGVLcTBnSXRjeEMyK3N4TmhyaCtoS01sYmRJWmowS1RZd2NOb0poNmE0ZkM3aTYKUVZQQmdrc01EMWNXUkJRblVqYytNNDd3TzNPZUs5TlFFUjNaVlVwR3ZwZkx1aThZaHlhVDYrbjdyRVZOU2hiSAplSzU5Q1E3UVo5ZVNjckJaYXBNakVCVkwxQnJPK1hsYWw2eU0yTVI2Z092OXNWdUQ5eXhya1FCbTdvZStuYmlOCjFhTHBzbVVmSG1PeW9QOEdab3doN2huekZyZUx4M25PM3o1SWJlaGxqZllKQWdNQkFBRT0KLS0tLS1FTkQgUFVCTElDIEtFWS0tLS0tCg=="
EXPECTED_RESULT_COLLECTOR_HASH="7f9a26c8e38f2c806f52c99cfe2f90f93963c808f16131b8f8adb07cdd4e7e84"
GOOGLE_CLOUD_PROJECT="data-owner-cc"
docker run --rm -v /home/hasan/.config/gcloud:/root/.config/gcloud:ro \
    -e DRY_RUN=1 \
    -e GOOGLE_CLOUD_PROJECT="$GOOGLE_CLOUD_PROJECT" \
    -e DATA_CONFIG="$DATA_CONFIG" \
    -e EXPECTED_DATA_HASH="$EXPECTED_DATA_HASH" \
    -e MODEL_CONFIG="$MODEL_CONFIG" \
    -e EXPECTED_MODEL_HASH="$EXPECTED_MODEL_HASH" \
    -e RESULT_CONFIG="$RESULT_CONFIG" \
    -e RESULT_COLLECTOR="$RESULT_COLLECTOR" \
    -e EXPECTED_RESULT_COLLECTOR_HASH="$EXPECTED_RESULT_COLLECTOR_HASH" \
    mlcommons/medperf-confidential-benchmark-base:0.0.0

