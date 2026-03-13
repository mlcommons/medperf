import google.auth
from medperf.asset_management.checks_utils import (
    check_user_role_on_bucket,
    check_user_role_on_service_account,
)


def verify_operator_setup(sa_email, bucket_name):
    base_creds, _ = google.auth.default()

    result = check_user_role_on_service_account(
        base_creds,
        sa_email,
        "roles/iam.serviceAccountUser",
    )
    if result:
        return False, result

    result = check_user_role_on_bucket(
        "user",
        base_creds,
        bucket_name,
        "roles/storage.objectViewer",
    )
    if result:
        return False, result

    return True, ""
