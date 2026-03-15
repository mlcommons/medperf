set -eo pipefail

KEYRING_NAME="medperf-keyring"
KEY_NAME="medperf-key"
KEY_LOCATION="global"
USER="hasan.gcptest@gmail.com"
PROJECT_ID="medperf-cc-test"
WIP_ID="medperf-wip"
WIP_PROVIDER_ID="medperf-wippro"
BUCKET_NAME="medperf-bucket"
BUCKET_LOCATION="us-central1"

####################################################
#################### Enable Services ###############
####################################################

gcloud services enable \
    cloudkms.googleapis.com \
    iamcredentials.googleapis.com

####################################################
#################### KMS ###########################
####################################################

FULL_KEY_NAME="projects/$PROJECT_ID/locations/$KEY_LOCATION/keyRings/$KEYRING_NAME/cryptoKeys/$KEY_NAME"

# Create Keyring
gcloud kms keyrings create "$KEYRING_NAME" \
    --location="$KEY_LOCATION"

# Create Key
gcloud kms keys create "$KEY_NAME" \
    --location="$KEY_LOCATION" \
    --keyring="$KEYRING_NAME" \
    --purpose=encryption \
    --protection-level=hsm

# allow user to encrypt with the key
gcloud kms keys add-iam-policy-binding "$FULL_KEY_NAME" \
    --member=user:"$USER" \
    --role="roles/cloudkms.cryptoKeyEncrypter"

# allow user to manage iam policy of the key
gcloud kms keys add-iam-policy-binding "$FULL_KEY_NAME" \
    --member=user:"$USER" \
    --role="roles/cloudkms.admin"

####################################################
#################### WIP ###########################
####################################################

# Create Workload Identity Pool
gcloud iam workload-identity-pools create "$WIP_ID" --location=global

# Create OIDC provider for WIP
gcloud iam workload-identity-pools providers create-oidc "$WIP_PROVIDER_ID" \
    --location=global \
    --workload-identity-pool="$WIP_ID" \
    --issuer-uri="https://confidentialcomputing.googleapis.com/" \
    --allowed-audiences="https://sts.googleapis.com" \
    --attribute-mapping="google.subject=\"gcpcs\
::\"+assertion.submods.container.image_digest+\"\
::\"+assertion.submods.gce.project_number+\"\
::\"+assertion.submods.gce.instance_id" \
    --attribute-condition="assertion.swname == 'CONFIDENTIAL_SPACE'"

# Allow user to manage WIP
gcloud iam workload-identity-pools add-iam-policy-binding "$WIP_ID" \
  --location=global \
  --project="$PROJECT_ID" \
  --member=user:"$USER" \
  --role="roles/iam.workloadIdentityPoolAdmin"


####################################################
#################### Bucket ########################
####################################################

# Create a bucket
gcloud storage buckets create "gs://$BUCKET_NAME" \
    --location="$BUCKET_LOCATION" \
    --uniform-bucket-level-access

# Allow user to manage the bucket
gcloud storage buckets add-iam-policy-binding "gs://$BUCKET_NAME" \
    --member=user:"$USER" \
    --role="roles/storage.admin"