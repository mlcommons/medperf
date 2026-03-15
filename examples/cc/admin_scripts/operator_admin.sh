export SERVICE_ACCOUNT_NAME="medperf-cc-sa"
export BUCKET_NAME="medperf-bucket"
export BUCKET_LOCATION="us-central1"
export USER="hasan.gcptest@gmail.com"

export VM_NAME="gputest"
export CC_TYPE="TDX"
export BOOT_DISK_SIZE="500GB"
export VM_ZONE="us-central1-a"
export VM_NETWORK="medperf-brats-network"
export MIN_CPU_PLATFORM="Intel Sapphire Rapids"
export MACHINE_TYPE="c3-standard-22"


SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"



####################################################
#################### Bucket ########################
####################################################

# Create a bucket
gcloud storage buckets create "gs://$BUCKET_NAME" \
    --location="$BUCKET_LOCATION"

# Allow user to manage the bucket
gcloud storage buckets add-iam-policy-binding "gs://$BUCKET_NAME" \
    --member=user:"$USER" \
    --role="roles/storage.objectViewer"

####################################################
#################### Enable Services ###############
####################################################

gcloud services enable \
    compute.googleapis.com \
    confidentialcomputing.googleapis.com \
    iamcredentials.googleapis.com


# create service account
gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME"

# allow user to use the service account
gcloud iam service-accounts add-iam-policy-binding \
    "$SERVICE_ACCOUNT_EMAIL" \
    --member=user:"$USER" \
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

####################################################
#################### Virtual Machine ###############
####################################################

# Create the VM
gcloud compute instances create "$VM_NAME" \
        --confidential-compute-type="$CC_TYPE" \
        --shielded-secure-boot \
        --scopes=cloud-platform \
        --boot-disk-size="$BOOT_DISK_SIZE" \
        --zone="$VM_ZONE" \
        --network="$VM_NETWORK" \
        --maintenance-policy=TERMINATE \
        --min-cpu-platform="$MIN_CPU_PLATFORM" \
        --image-project=confidential-space-images \
        --image-family=confidential-space \
        --machine-type="$MACHINE_TYPE" \
        --service-account="$SERVICE_ACCOUNT_EMAIL"

# allow user to edit the VM metadata
gcloud compute instances add-iam-policy-binding "$VM_NAME" \
    --zone="$VM_ZONE" \
    --member=user:"$USER" \
    --role="roles/compute.instanceAdmin.v1"