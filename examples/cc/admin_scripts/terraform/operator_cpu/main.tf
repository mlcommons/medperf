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
  service_account_email = "${local.service_account_name}@${local.project_id}.iam.gserviceaccount.com"
  service_account_id    = "projects/${local.project_id}/serviceAccounts/${local.service_account_email}"
  image                 = "projects/confidential-space-images/global/images/family/confidential-space"
}

resource "google_project_service" "this" {
  for_each = local.enable_services ? toset([
    "compute.googleapis.com",
    "confidentialcomputing.googleapis.com",
    "iamcredentials.googleapis.com",
    "iam.googleapis.com",
  ]) : toset([])

  project            = local.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_service_account" "workload" {
  count = local.create_service_account ? 1 : 0

  account_id = local.service_account_name
  project    = local.project_id
  depends_on = [google_project_service.this]
}

resource "google_service_account_iam_member" "user" {
  service_account_id = local.service_account_id
  role               = "roles/iam.serviceAccountUser"
  member             = local.member
  depends_on         = [google_service_account.workload]
}

resource "google_project_iam_member" "workload_user" {
  project    = local.project_id
  role       = "roles/confidentialcomputing.workloadUser"
  member     = "serviceAccount:${local.service_account_email}"
  depends_on = [google_service_account.workload]
}

resource "google_project_iam_member" "log_writer" {
  project    = local.project_id
  role       = "roles/logging.logWriter"
  member     = "serviceAccount:${local.service_account_email}"
  depends_on = [google_service_account.workload]
}

resource "google_compute_network" "this" {
  count = local.create_network ? 1 : 0

  name                    = local.vm_network
  project                 = local.project_id
  auto_create_subnetworks = true
  depends_on              = [google_project_service.this]
}

resource "google_compute_instance" "this" {
  count = local.create_vm ? 1 : 0

  name             = local.vm_name
  project          = local.project_id
  zone             = local.vm_zone
  machine_type     = local.machine_type
  min_cpu_platform = local.min_cpu_platform
  desired_status   = "TERMINATED"

  boot_disk {
    initialize_params {
      image = local.image
      size  = local.boot_disk_size
      type  = local.boot_disk_type
    }
  }

  network_interface {
    network = local.vm_network

    access_config {}
  }

  confidential_instance_config {
    confidential_instance_type = "TDX"
  }

  shielded_instance_config {
    enable_secure_boot = true
  }

  scheduling {
    on_host_maintenance = "TERMINATE"
  }

  service_account {
    email  = local.service_account_email
    scopes = ["cloud-platform"]
  }

  depends_on = [google_service_account.workload, google_compute_network.this]

  # MedPerf sets the workload metadata and starts the machine on every run.
  lifecycle {
    ignore_changes = [metadata, desired_status]
  }
}

resource "google_compute_instance_iam_member" "instance_admin" {
  project       = local.project_id
  zone          = local.vm_zone
  instance_name = local.vm_name
  role          = "roles/compute.instanceAdmin.v1"
  member        = local.member
  depends_on    = [google_compute_instance.this]
}

output "info" {
  value = <<-EOT

    Information to be passed to the user:

    Project ID:                  ${local.project_id}
    Service Account Name:        ${local.service_account_name}
    VM Zone:                     ${local.vm_zone}
    VM Name:                     ${local.vm_name}
  EOT
}
