locals {
  project_id = "my-project"

  # Who will use MedPerf. A person, or a service account:
  #   "user:someone@example.com"
  #   "serviceAccount:name@my-project.iam.gserviceaccount.com"
  member = "user:someone@example.com"

  keyring_name = "my-keyring"
  key_name     = "my-key"
  key_location = "us-west1"

  wip_id          = "my-wip"
  wip_provider_id = "attestation-verifier"

  bucket_name     = "my-globally-unique-bucket"
  bucket_location = "us-west1"

  # Set any of these to false to use something that already exists under that
  # name instead of creating it. The permissions are granted either way.
  enable_services     = true
  create_keyring      = true
  create_key          = true
  create_wip          = true
  create_wip_provider = true
  create_bucket       = true
}
