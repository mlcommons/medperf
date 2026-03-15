# CC Requirements

## For GCP Project Admin

### Quotas

You will be creating:

- bucket
- a KMS HSM key
- a workload identity pool
- a service account
- a GPU-based confidential VM (machine type: a3-highgpu-1g). To view zones where this machine type is available, visit <https://docs.cloud.google.com/compute/docs/regions-zones/gpu-regions-zones> and look for availability of "A3 High".

You will need to make sure you have enough quota for nvidia h100 GPUs:

- visit <https://docs.cloud.google.com/confidential-computing/confidential-vm/docs/create-a-confidential-vm-instance-with-gpu#request-preemptible-quota> and read sections "Request preemptible quota" and "Request global quota"; make sure you have these quotas. only 1 GPU is needed.

### Creating resources

Note: a script `admin.sh` can be found in this folder. You can configure the constants (e.g., project id, names of the resources to be created, etc...), run the script in cloud shell, and you are done. It will print at the end the information needed to be passed to the user.

If you want to create resources manually, follow the instructions below.

#### Resources for Hosting the dataset and managing access

- Create a bucket
  - Uniform Bucket Level Access must be enabled. (In bucket configuration tab, edit permissions.access_control: change from fine grained to uniform)
  - grant the user "roles/storage.admin" for the bucket

- Create a keyring
  - select a suitable region (this may relate to compliance/regulations requirements)

- Create a key in the keyring
  - Choose protection level to be HSM
  - grant the user "roles/cloudkms.cryptoKeyEncrypter" for the key
  - grant the user "roles/cloudkms.admin" for the key

- create a workload identity pool
  - add name and description...
  - add OIDC provider
    choose issuer-uri to be <https://confidentialcomputing.googleapis.com/>
    choose allowed-audiences to be <https://sts.googleapis.com>
  - add the following as the google.subject attribute:
    - "gcpcs::"+assertion.submods.container.image_digest+"::"+assertion.submods.gce.project_number+"::"+assertion.submods.gce.instance_id
  - click create/save
  - grant user update permissions for the wip
    - You should use the commnad provided in the `admin.sh` file in this folder. Run it in the cloud shell.

#### Resources for operating a CVM

<!-- This is commented currently because the data owner and the operator are the same user -->
<!-- - Create a bucket
  - Uniform Bucket Level Access must be enabled. (In bucket configuration tab, edit permissions.access_control: change from fine grained to uniform)
  - grant the user "roles/storage.objectViewer" for the bucket -->

- Create a service account
  - grant the user "roles/iam.serviceAccountUser" for the service account
  - grant the service account "roles/confidentialcomputing.workloadUser" for the project
  - grant the service account "roles/logging.logWriter" for the project
  - grant the service account "roles/storage.objectAdmin" for the bucket

- Create a VM
  - You should use the command given in the `admin.sh` script to create the VM. Run it in the cloud shell.
  - grant the user "roles/compute.instanceAdmin.v1" role on the VM.

## For users

login
set project
run `gcloud auth application-default login`
