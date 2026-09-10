locals {
  project_id = "my-project"

  # Who will use MedPerf. A person, or a service account:
  #   "user:someone@example.com"
  #   "serviceAccount:name@my-project.iam.gserviceaccount.com"
  member = "user:someone@example.com"

  service_account_name = "my-workload-sa"

  vm_name    = "my-vm"
  vm_zone    = "us-central1-a"
  vm_network = "default"

  machine_type = "a3-highgpu-1g"

  boot_disk_size = 500
  boot_disk_type = "pd-balanced"

  max_run_duration_seconds = 86400

  # Set any of these to false to use something that already exists under that
  # name instead of creating it. The permissions are granted either way.
  enable_services        = true
  create_service_account = true
  create_network         = false
  create_vm              = true
}
