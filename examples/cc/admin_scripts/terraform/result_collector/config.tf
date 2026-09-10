locals {
  project_id = "my-project"

  # Who will use MedPerf. A person, or a service account:
  #   "user:someone@example.com"
  #   "serviceAccount:name@my-project.iam.gserviceaccount.com"
  member = "user:someone@example.com"

  bucket_name     = "my-globally-unique-bucket"
  bucket_location = "us-west1"

  # The service account of the VM that will write results here. It is the
  # operator's service_account_name, as <name>@<project>.iam.gserviceaccount.com.
  workload_service_account_email = "my-workload-sa@my-project.iam.gserviceaccount.com"

  # Set to false to use a bucket that already exists under that name instead
  # of creating it. The permissions are granted either way.
  create_bucket = true
}
