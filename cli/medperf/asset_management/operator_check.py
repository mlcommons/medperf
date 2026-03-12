import google.auth
from medperf.asset_management.checks_utils import (
    check_user_role_on_bucket,
    check_sa_roles_for_project,
    check_user_role_on_service_account,
    impersonate_service_account,
    check_user_role_on_vm,
)


def verify_operator_setup(sa_email, project_id, bucket_name):
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

    sa_creds = impersonate_service_account(base_creds, sa_email)
    if not sa_creds:
        return False, f"Failed to impersonate service account: {sa_email}"

    result = check_sa_roles_for_project(
        sa_creds,
        project_id,
        "roles/confidentialcomputing.workloadUser",
    )
    if result:
        return False, result

    result = check_sa_roles_for_project(
        sa_creds,
        project_id,
        "roles/logging.logWriter",
    )
    if result:
        return False, result

    result = check_user_role_on_bucket(
        "service account",
        sa_creds,
        bucket_name,
        "roles/storage.objectAdmin",
    )
    if result:
        return False, result

    result = check_user_role_on_vm(
        base_creds,
        project_id,
        vm_name,
        vm_zone,
        "roles/compute.instanceAdmin.v1",
    )
    if result:
        return False, result

    return True, ""
