# CC Requirements

## any user

login
set project
run `gcloud auth application-default login`

## Operator

- Create a service account
- grant the user "roles/iam.serviceAccountUser" for the service account
- grant the service account "roles/confidentialcomputing.workloadUser" for the project  # important
- grant the service account "roles/logging.logWriter" for the project  # important

- Create a bucket, Uniform Bucket Level Access must be enabled. (permissions.access_control change from fine grained to uniform, and add existing project roles.)
- grant the user "roles/storage.objectViewer" for the bucket
- grant the service account "roles/storage.objectAdmin" for the bucket  # important

- Create a VM
  - choose name and zone
  - choose c3-highmem-8 (8 vCPU, 4 core, 64 GB memory)
  - advanced configurations, and CPU platform: Intel Sapphire Rapids or later
  -
- grant the user "roles/compute.instanceAdmin.v1" role on the VM.

## asset owner

- Create a bucket, Uniform Bucket Level Access must be enabled. (permissions.access_control change from fine grained to uniform, and add existing project roles.)
- grant the user ("roles/storage.admin") to the bucket
<!-- - grant the user write access ("roles/storage.objectAdmin") to the bucket -->

- create a keyring
  - select region
- create a key
  - software (default)
- grant the user "roles/cloudkms.cryptoKeyEncrypter" for the key
- grant the user "roles/cloudkms.admin" for the key
- create a workload identity pool
  - add name and description

  - add OIDC provider
        "--issuer-uri=<https://confidentialcomputing.googleapis.com/>",
    "--allowed-audiences=<https://sts.googleapis.com>",

  - select name and ID to be attestation-verifier
  - add the following as the google subject:
    - "gcpcs::"+assertion.submods.container.image_digest+"::"+assertion.submods.gce.project_number+"::"+assertion.submods.gce.instance_id

  - click create/save

- grant user update permissions for the wip:

gcloud iam workload-identity-pools add-iam-policy-binding POOL_NAME \
  --location=global \
  --project=PROJECT_ID \
  --member="user:USER_EMAIL" \
  --role="roles/iam.workloadIdentityPoolAdmin"
 <!-- TODO: test what happens if service account doesn't have enough permissions on the project -->
