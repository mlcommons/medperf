import google.auth
from medperf.asset_management.checks_utils import (
    check_user_role_on_bucket,
    check_user_role_on_kms_key,
    check_user_role_on_wip,
)
from google.auth.credentials import AnonymousCredentials


def verify_asset_owner_setup(bucket_name, kms_key_resource, wip_resource):
    base_creds, _ = google.auth.default()
    result = check_user_role_on_bucket(
        "user",
        base_creds,
        bucket_name,
        "roles/storage.objectAdmin",
    )
    if result:
        return False, result

    result = check_user_role_on_kms_key(
        base_creds,
        kms_key_resource,
        "roles/cloudkms.cryptoKeyEncrypter",
    )

    if result:
        return False, result

    result = check_user_role_on_kms_key(
        base_creds,
        kms_key_resource,
        "roles/cloudkms.admin",
    )

    if result:
        return False, result

    anon_creds = AnonymousCredentials()

    result = check_user_role_on_bucket(
        "anonymous user",
        anon_creds,
        bucket_name,
        "roles/storage.objectViewer",
    )
    if result:
        return False, result

    result = check_user_role_on_wip(
        base_creds,
        wip_resource,
        "roles/iam.workloadIdentityPoolAdmin",
    )

    return True, ""
