from medperf.asset_management.gcp_utils import checks, get_user_credentials


def verify_operator_setup(sa_email, bucket_name):
    base_creds = get_user_credentials()
    result = checks.check_user_role_on_service_account(
        base_creds,
        sa_email,
        "roles/iam.serviceAccountUser",
    )
    if result:
        return False, result

    result = checks.check_user_role_on_bucket(
        "user",
        base_creds,
        bucket_name,
        "roles/storage.objectViewer",
    )
    if result:
        return False, result

    return True, ""
