terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
  }
}

provider "google" {
  project = local.project_id
}

locals {
  keyring_id  = "projects/${local.project_id}/locations/${local.key_location}/keyRings/${local.keyring_name}"
  key_id      = "${local.keyring_id}/cryptoKeys/${local.key_name}"
  wip_full_id = "projects/${local.project_id}/locations/global/workloadIdentityPools/${local.wip_id}"
}

data "google_project" "this" {
  project_id = local.project_id
}

resource "google_project_service" "this" {
  for_each = local.enable_services ? toset([
    "cloudkms.googleapis.com",
    "iamcredentials.googleapis.com",
    "iam.googleapis.com",
  ]) : toset([])

  project            = local.project_id
  service            = each.value
  disable_on_destroy = false
}

# GCP cannot delete keyrings or keys.
resource "google_kms_key_ring" "this" {
  count = local.create_keyring ? 1 : 0

  name       = local.keyring_name
  location   = local.key_location
  project    = local.project_id
  depends_on = [google_project_service.this]

  lifecycle {
    prevent_destroy = true
  }
}

resource "google_kms_crypto_key" "this" {
  count = local.create_key ? 1 : 0

  name     = local.key_name
  key_ring = local.keyring_id
  purpose  = "ENCRYPT_DECRYPT"

  version_template {
    algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
    protection_level = "HSM"
  }

  depends_on = [google_kms_key_ring.this]

  lifecycle {
    prevent_destroy = true
  }
}

resource "google_kms_crypto_key_iam_member" "encrypter" {
  crypto_key_id = local.key_id
  role          = "roles/cloudkms.cryptoKeyEncrypter"
  member        = local.member
  depends_on    = [google_kms_crypto_key.this]
}

resource "google_kms_crypto_key_iam_member" "admin" {
  crypto_key_id = local.key_id
  role          = "roles/cloudkms.admin"
  member        = local.member
  depends_on    = [google_kms_crypto_key.this]
}

resource "google_iam_workload_identity_pool" "this" {
  count = local.create_wip ? 1 : 0

  workload_identity_pool_id = local.wip_id
  project                   = local.project_id
  depends_on                = [google_project_service.this]
}

resource "google_iam_workload_identity_pool_provider" "this" {
  count = local.create_wip_provider ? 1 : 0

  project                            = local.project_id
  workload_identity_pool_id          = local.wip_id
  workload_identity_pool_provider_id = local.wip_provider_id

  attribute_mapping = {
    "google.subject" = join("", [
      "\"gcpcs::\"+assertion.submods.container.image_digest",
      "+\"::\"+assertion.submods.gce.project_number",
      "+\"::\"+assertion.submods.gce.instance_id",
    ])
  }

  attribute_condition = "assertion.swname == 'CONFIDENTIAL_SPACE'"

  oidc {
    issuer_uri        = "https://confidentialcomputing.googleapis.com/"
    allowed_audiences = ["https://sts.googleapis.com"]
  }

  depends_on = [google_iam_workload_identity_pool.this]

  # MedPerf rewrites these every time an asset is published.
  lifecycle {
    ignore_changes = [attribute_mapping, attribute_condition]
  }
}

# The Google provider has no resource for IAM on a workload identity pool.
resource "terraform_data" "wip_admin" {
  input = {
    pool    = local.wip_id
    project = local.project_id
    member  = local.member
  }

  triggers_replace = [local.wip_full_id, local.member]

  provisioner "local-exec" {
    command = <<-EOT
      gcloud iam workload-identity-pools add-iam-policy-binding "${self.input.pool}" \
        --location=global \
        --project="${self.input.project}" \
        --member="${self.input.member}" \
        --role="roles/iam.workloadIdentityPoolAdmin"
    EOT
  }

  depends_on = [google_iam_workload_identity_pool.this]
}

resource "google_storage_bucket" "this" {
  count = local.create_bucket ? 1 : 0

  name                        = local.bucket_name
  location                    = local.bucket_location
  project                     = local.project_id
  uniform_bucket_level_access = true
}

resource "google_storage_bucket_iam_member" "admin" {
  bucket     = local.bucket_name
  role       = "roles/storage.admin"
  member     = local.member
  depends_on = [google_storage_bucket.this]
}

output "info" {
  value = <<-EOT

    Information to be passed to the user:

    Project ID:                  ${local.project_id}
    Project Number:              ${data.google_project.this.number}
    Bucket:                      ${local.bucket_name}
    Keyring Name:                ${local.keyring_name}
    Key Name:                    ${local.key_name}
    Key Location:                ${local.key_location}
    Workload Identity Pool:      ${local.wip_id}
    Workload Identity Provider:  ${local.wip_provider_id}
  EOT
}
