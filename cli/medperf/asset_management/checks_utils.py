import logging
import googleapiclient.discovery


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def get_testable_permissions(resource):
    if resource.startswith("//cloudresourcemanager"):
        # don't find testable permissions for cloudresourcemanager
        # Since they are a lot.
        return {
            "confidentialcomputing.challenges.create",
            "confidentialcomputing.challenges.verify",
            "confidentialcomputing.locations.get",
            "confidentialcomputing.locations.list",
            "logging.logEntries.create",
            "logging.logEntries.route",
        }
    if "workloadIdentityPools" in resource:
        # doesn't seem to have an api for this
        return {
            "iam.googleapis.com/workloadIdentityPoolProviders.update",
            "iam.googleapis.com/workloadIdentityPoolProviders.get",
            "iam.googleapis.com/workloadIdentityPools.get",
        }

    iam = googleapiclient.discovery.build("iam", "v1")
    resp = (
        iam.permissions()
        .queryTestablePermissions(body={"fullResourceName": resource, "pageSize": 1000})
        .execute()
    )
    return set(p["name"] for p in resp.get("permissions", []))


def get_role_permissions(role_name: str, resource: str):
    if role_name == "roles/storage.objectAdmin":
        # storage permissions are not fully reflected in the role definition, so we hardcode them here
        return [
            "storage.objects.create",
            "storage.objects.delete",
            "storage.objects.get",
            "storage.objects.list",
        ]
    if role_name == "roles/storage.admin":
        # storage permissions are not fully reflected in the role definition, so we hardcode them here
        return [
            "storage.objects.create",
            "storage.objects.delete",
            "storage.objects.get",
            "storage.objects.list",
            "storage.buckets.setIamPolicy",
            "storage.buckets.getIamPolicy",
        ]
    if role_name == "roles/compute.instanceAdmin.v1":
        return [
            "compute.instances.setMetadata",
            "compute.instances.start",
            "compute.instances.get",
            "compute.instances.getSerialPortOutput",
        ]
    service = googleapiclient.discovery.build("iam", "v1")
    role = service.roles().get(name=role_name).execute()
    permissions = role.get("includedPermissions", [])
    testable = get_testable_permissions(resource)
    return list(testable.intersection(permissions))


# ---------------------------------------------------------------------------
# User roles
# ---------------------------------------------------------------------------
def check_user_role_on_service_account(base_creds, sa_email, role):
    logging.debug(f"Checking if user has {role} role on {sa_email}")
    try:
        permissions = get_role_permissions(
            role, "//iam.googleapis.com/projects/_/serviceAccounts/_"
        )
        iam = googleapiclient.discovery.build(
            "iam", "v1", credentials=base_creds, cache_discovery=False
        )
        granted = (
            iam.projects()
            .serviceAccounts()
            .testIamPermissions(
                resource=f"projects/-/serviceAccounts/{sa_email}",
                body={"permissions": permissions},
            )
            .execute()
        )
        granted_permissions = granted.get("permissions", [])
        missing = set(permissions) - set(granted_permissions)
        if missing:
            logging.debug(f"Missing permissions: {missing}")
            return f"(Role {role}) User missing permissions: {missing} on service account: {sa_email}"
        return None
    except Exception as e:
        logging.debug(f"check_user_role_on_service_account exception: {e}")
        return f"Failed to verify user role on service account: {sa_email}"


def check_user_role_on_bucket(user_str, creds, bucket_name, role):

    logging.debug(f"Checking if {user_str} has {role} role on bucket: {bucket_name}")
    try:
        permissions = get_role_permissions(
            role, "//storage.googleapis.com/projects/_/buckets/_"
        )
        iam = googleapiclient.discovery.build(
            "storage", "v1", credentials=creds, cache_discovery=False
        )
        granted = (
            iam.buckets()
            .testIamPermissions(bucket=bucket_name, permissions=permissions)
            .execute()
        )
        granted_permissions = granted.get("permissions", [])
        missing = set(permissions) - set(granted_permissions)
        if missing:
            logging.debug(f"Missing permissions: {missing}")
            return f"(Role {role}) {user_str} missing permissions: {missing} on bucket: {bucket_name}"
        return None
    except Exception as e:
        logging.debug(f"check_user_role_on_bucket exception: {e}")
        return f"Failed to verify {user_str} role on bucket: {bucket_name}"


# ---------------------------------------------------------------------------
# KMS roles
# ---------------------------------------------------------------------------


def check_user_role_on_kms_key(base_creds, kms_key_resource, role):
    logging.debug(f"Checking user role {role} on KMS key {kms_key_resource}")

    try:
        kms = googleapiclient.discovery.build(
            "cloudkms", "v1", credentials=base_creds, cache_discovery=False
        )

        permissions = get_role_permissions(
            role,
            "//cloudkms.googleapis.com/projects/_/locations/_/keyRings/_/cryptoKeys/_",
        )

        granted = (
            kms.projects()
            .locations()
            .keyRings()
            .cryptoKeys()
            .testIamPermissions(
                resource=kms_key_resource,
                body={"permissions": permissions},
            )
            .execute()
        )

        granted_permissions = granted.get("permissions", [])
        missing = set(permissions) - set(granted_permissions)

        if missing:
            return f"(Role {role}) User missing permissions: {missing} on KMS key {kms_key_resource}"

        return None

    except Exception as e:
        logging.debug(f"KMS permission check failed: {e}")
        return f"Failed verifying user roles on KMS key {kms_key_resource}"


# ---------------------------------------------------------------------------
# WIP roles
# ---------------------------------------------------------------------------


def check_user_role_on_wip(creds, wip, role):

    logging.debug(f"Checking user role {role} on WIP {wip}")

    try:
        iam = googleapiclient.discovery.build(
            "iam", "v1", credentials=creds, cache_discovery=False
        )

        permissions = get_role_permissions(
            role, "//iam.googleapis.com/projects/_/locations/_/workloadIdentityPools/_"
        )

        granted = (
            iam.projects()
            .locations()
            .workloadIdentityPools()
            .testIamPermissions(
                resource=wip,
                body={"permissions": permissions},
            )
            .execute()
        )

        granted_permissions = granted.get("permissions", [])
        missing = set(permissions) - set(granted_permissions)

        if missing:
            return f"(Role {role}) User missing permissions: {missing} on WIP {wip}"

        return None

    except Exception as e:
        logging.debug(f"WIP permission check failed: {e}")
        return f"Failed verifying user roles on WIP {wip}"


# ---------------------------------------------------------------------------
# VM roles
# ---------------------------------------------------------------------------


def check_user_role_on_vm(user_str, creds, project_id, vm_name, vm_zone, role):

    logging.debug(f"Checking if {user_str} has {role} role on VM: {vm_name}")
    try:
        permissions = get_role_permissions(
            role,
            "//compute.googleapis.com/projects/_/zones/_/instances/_",
        )
        compute = googleapiclient.discovery.build(
            "compute", "v1", credentials=creds, cache_discovery=False
        )
        granted = (
            compute.instances()
            .testIamPermissions(
                project=project_id,
                zone=vm_zone,
                resource=vm_name,
                body={"permissions": permissions},
            )
            .execute()
        )
        granted_permissions = granted.get("permissions", [])
        missing = set(permissions) - set(granted_permissions)
        if missing:
            logging.debug(f"Missing permissions: {missing}")
            return f"(Role {role}) {user_str} missing permissions: {missing} on VM: {vm_name}"
        return None
    except Exception as e:
        logging.debug(f"check_user_role_on_vm exception: {e}")
        return f"Failed to verify {user_str} role on VM: {vm_name}"
