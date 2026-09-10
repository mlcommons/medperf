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

resource "google_storage_bucket_iam_member" "workload" {
  bucket     = local.bucket_name
  role       = "roles/storage.objectAdmin"
  member     = "serviceAccount:${local.workload_service_account_email}"
  depends_on = [google_storage_bucket.this]
}

output "info" {
  value = <<-EOT

    Information to be passed to the user:

    Project ID:                  ${local.project_id}
    Bucket:                      ${local.bucket_name}
  EOT
}
