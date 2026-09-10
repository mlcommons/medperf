# CC Requirements

## For GCP Project Admin

Context: The user will use the MedPerf client on the local machine where the model resides. You (IT/cloud admin) will be creating required resources for the model user in order to allow them to use MedPerf to run inference using their model in a confidential virtual machine on google cloud. Here is what will happen behind the scenes when the user uses MedPerf to run a confidential computing workload; this will help understand the reason behind the resources and user roles being asked for.

Medperf will:

1. Encrypt the model using a locally generated key.
2. Encrypt the key using cloud KMS
3. Upload the encrypted model and the encrypted key to the cloud bucket.
4. Update the workload identity pool OIDC provider with relevant attribute conditions and configure it to bind certain attestation claims to identities.
5. Update the IAM policy of the bucket and of the KMS to only allow a confidential computing workload with certain attestation claims to get the encrypted model and to use the KMS to decrypt.

### Quotas

You will be creating:

- a bucket
- a KMS HSM key
- a workload identity pool and an OIDC provider.

### Creating resources

The Terraform configurations in `terraform/` create everything. This user needs `asset_owner` only. See `terraform/README.md`.
