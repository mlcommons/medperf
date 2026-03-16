set -eo pipefail
####################################################
#################### Config ########################
####################################################

# Project ID
export PROJECT_ID="medperf-330914"

# User email
export USER_EMAIL="hasan.gcptest@gmail.com"

# New service account name to create
export SERVICE_ACCOUNT_NAME="cc-test"

# New KMS info to create
export KEYRING_NAME="data-owner-keyring"
export KEY_NAME="data-owner-cc-key"
export KEY_LOCATION="global"

# New Workload identity pool and OIDC provider info to create
export WIP_ID="test1"
export WIP_PROVIDER_ID="attestation-verifier"

# New bucket info to create
export BUCKET_NAME="medperf-bucket"
export BUCKET_LOCATION="us-central1"

# New virtual machine info to create
export VM_NAME="gputestdebug"
export BOOT_DISK_SIZE="500GB"
export VM_ZONE="us-central1-a"
export VM_NETWORK="medperf-brats-network"  # default is usually "default"

####################################################
#################### End Config ####################
####################################################

# some more global vars
export FULL_KEY_NAME="projects/$PROJECT_ID/locations/$KEY_LOCATION/keyRings/$KEYRING_NAME/cryptoKeys/$KEY_NAME"
export SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"

####################################################
#################### Enable Services ###############
####################################################

gcloud services enable \
    cloudkms.googleapis.com \
    compute.googleapis.com \
    confidentialcomputing.googleapis.com \
    iamcredentials.googleapis.com

echo "********************************************************************************************"
echo "************************************* Services enabled *************************************"
echo "********************************************************************************************"
####################################################
#################### KMS ###########################
####################################################


# Create Keyring
gcloud kms keyrings create "$KEYRING_NAME" \
    --location="$KEY_LOCATION"

echo "********************************************************************************************"
echo "************************************* KMS Keyring created **********************************"
echo "********************************************************************************************"

# Create Key
gcloud kms keys create "$KEY_NAME" \
    --location="$KEY_LOCATION" \
    --keyring="$KEYRING_NAME" \
    --purpose=encryption \
    --protection-level=hsm

echo "********************************************************************************************"
echo "************************************* KMS Key created **************************************"
echo "********************************************************************************************"

# allow user to encrypt with the key
gcloud kms keys add-iam-policy-binding "$FULL_KEY_NAME" \
    --member=user:"$USER_EMAIL" \
    --role="roles/cloudkms.cryptoKeyEncrypter"

# allow user to manage iam policy of the key
gcloud kms keys add-iam-policy-binding "$FULL_KEY_NAME" \
    --member=user:"$USER_EMAIL" \
    --role="roles/cloudkms.admin"

echo "********************************************************************************************"
echo "************************************* KMS permissions granted ******************************"
echo "********************************************************************************************"

####################################################
#################### WIP ###########################
####################################################

# Create Workload Identity Pool
gcloud iam workload-identity-pools create "$WIP_ID" --location=global

echo "********************************************************************************************"
echo "************************************* WIP created ******************************************"
echo "********************************************************************************************"

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


echo "********************************************************************************************"
echo "************************************* WIP provider created *********************************"
echo "********************************************************************************************"

# Allow user to manage WIP
gcloud iam workload-identity-pools add-iam-policy-binding "$WIP_ID" \
  --location=global \
  --project="$PROJECT_ID" \
  --member=user:"$USER_EMAIL" \
  --role="roles/iam.workloadIdentityPoolAdmin"


echo "********************************************************************************************"
echo "************************************* WIP permissions granted ******************************"
echo "********************************************************************************************"


####################################################
#################### Bucket ########################
####################################################

# Create a bucket
gcloud storage buckets create "gs://$BUCKET_NAME" \
    --location="$BUCKET_LOCATION" \
    --uniform-bucket-level-access


echo "********************************************************************************************"
echo "************************************* Bucket created ***************************************"
echo "********************************************************************************************"

# Allow user to manage the bucket
gcloud storage buckets add-iam-policy-binding "gs://$BUCKET_NAME" \
    --member=user:"$USER_EMAIL" \
    --role="roles/storage.admin"

echo "********************************************************************************************"
echo "************************************* Bucket permissions granted ***************************"
echo "********************************************************************************************"

####################################################
#################### Service Account ###############
####################################################

# create service account
gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME"

echo "********************************************************************************************"
echo "************************************* Service Account created ******************************"
echo "********************************************************************************************"

# allow user to use the service account
gcloud iam service-accounts add-iam-policy-binding \
    "$SERVICE_ACCOUNT_EMAIL" \
    --member=user:"$USER_EMAIL" \
    --role="roles/iam.serviceAccountUser"

# give the service account cc workload user role
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member=serviceAccount:"$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/confidentialcomputing.workloadUser"

# give the service account permissions to write logs
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member=serviceAccount:"$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/logging.logWriter"

# grant the service account permissions to write to the bucket
gcloud storage buckets add-iam-policy-binding "gs://$BUCKET_NAME" \
    --member=serviceAccount:"$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.objectAdmin"

echo "********************************************************************************************"
echo "********************** Service account permissions granted *********************************"
echo "********************************************************************************************"

####################################################
#################### Virtual Machine ###############
####################################################

# # Create the VM
# export CC_TYPE="TDX"
# export MIN_CPU_PLATFORM="Intel Sapphire Rapids"
# export MACHINE_TYPE="c3-standard-22"
# gcloud compute instances create "$VM_NAME" \
#         --confidential-compute-type="$CC_TYPE" \
#         --shielded-secure-boot \
#         --scopes=cloud-platform \
#         --boot-disk-size="$BOOT_DISK_SIZE" \
#         --zone="$VM_ZONE" \
#         --network="$VM_NETWORK" \
#         --maintenance-policy=TERMINATE \
#         --min-cpu-platform="$MIN_CPU_PLATFORM" \
#         --image-project=confidential-space-images \
#         --image-family=confidential-space \
#         --machine-type="$MACHINE_TYPE" \
#         --service-account="$SERVICE_ACCOUNT_EMAIL"

# Create GPU VM
gcloud compute instances create "$VM_NAME" \
    --provisioning-model=FLEX_START \
    --confidential-compute-type=TDX \
    --machine-type="a3-highgpu-1g" \
    --maintenance-policy=TERMINATE \
    --shielded-secure-boot \
    --image-project="confidential-space-images" \
    --image-family="confidential-space-preview-cgpu" \
    --service-account="$SERVICE_ACCOUNT_EMAIL" \
    --scopes=cloud-platform \
    --boot-disk-size="$BOOT_DISK_SIZE" \
    --zone="$VM_ZONE" \
    --network="$VM_NETWORK" \
    --max-run-duration=24h \
    --instance-termination-action=STOP \
    --discard-local-ssds-at-termination-timestamp=true

echo "********************************************************************************************"
echo "************************************* VM created *******************************************"
echo "********************************************************************************************"

# Stop the VM
gcloud compute instances stop "$VM_NAME" --zone="$VM_ZONE" --project="$PROJECT_ID" --discard-local-ssd=false

echo "********************************************************************************************"
echo "************************************* VM stopped *******************************************"
echo "********************************************************************************************"

# allow user to edit the VM metadata and to start it
gcloud compute instances add-iam-policy-binding "$VM_NAME" \
    --zone="$VM_ZONE" \
    --member=user:"$USER_EMAIL" \
    --role="roles/compute.instanceAdmin.v1"

echo "********************************************************************************************"
echo "************************************* VM permissions granted *******************************"
echo "********************************************************************************************"

# Give the user the following information

PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")

cat <<EOF
Information to be passed to the user:

Project ID:                  $PROJECT_ID
Project Number:              $PROJECT_NUMBER
Bucket:                      $BUCKET_NAME
Keyring Name:                $KEYRING_NAME
Key Name:                    $KEY_NAME
Key Location:                $KEY_LOCATION
Workload Identity Pool:      $WIP_ID
Workload Identity Provider:  $WIP_PROVIDER_ID
Service Account Name:        $SERVICE_ACCOUNT_NAME
VM Zone:                     $VM_ZONE
VM Name:                     $VM_NAME
EOF