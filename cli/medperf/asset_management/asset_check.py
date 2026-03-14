from medperf.asset_management.gcp_utils import checks, get_user_credentials


def verify_asset_owner_setup(bucket_name, kms_key_resource, wip_resource):
    base_creds = get_user_credentials()
    result = checks.check_user_role_on_bucket(
        "user",
        base_creds,
        bucket_name,
        "roles/storage.admin",
    )
    if result:
        return False, result

    result = checks.check_user_role_on_kms_key(
        base_creds,
        kms_key_resource,
        "roles/cloudkms.cryptoKeyEncrypter",
    )

    if result:
        return False, result

    result = checks.check_user_role_on_kms_key(
        base_creds,
        kms_key_resource,
        "roles/cloudkms.admin",
    )

    if result:
        return False, result

    result = checks.check_user_role_on_wip(
        base_creds,
        wip_resource,
        "roles/iam.workloadIdentityPoolAdmin",
    )

    if result:
        return False, result

    return True, ""
