# Configuring confidential Computing

This guide assumes that you already have a registered dataset, you prepared it, you set it operational, and you are associated with the benchmark that contains a model that requires confidential computing.
Note: associate your dataset with the new benchmark TODO.

## Configure you google cloud environment locally

You need to:

- Install the gcloud CLI (<https://docs.cloud.google.com/sdk/docs/install-sdk>)
- authenticate: `gcloud auth login`
- set project ID: `gcloud config set project PROJECT_ID`
- run `gcloud auth application-default login`

## Start the web UI and login

run `medperf_webui`
click on the `login` button.

## Get a certificate

Navigate to the `settings page` in the web UI and scroll down to the `Certificate Settings` section. If you already have a certificate, skip this step. Otherwise, click the button to get a certificate and follow the steps.

## Configure your cloud environment information in MedPerf

You should have recieved the following information from your google cloud administrator:

- Project ID
- Project Number
- Bucket
- Keyring Name
- Key Name
- Key Location
- Workload Identity Pool
- Workload Identity Provider
- Service Account Name
- VM Zone
- VM Name

You will use this information to configure your Medperf client.

### Configure your confidential VM settings

Navigate to the `settings` page in the web UI, scroll down to the `Confidential Computing Operator Settings`, check the box to `Configure confidential Computing` and fill in the required information. After that, click `Apply Changes`.

### Configure your Dataset cloud resources settings

Navigate to your dataset page (Datasets tab, then your dataset name. You can click `mine_only` to view only yours).

Then, scroll down to the section `Confidential Computing Preferences`. Check the box to `Configure dataset for Confidential Computing` and fill in the required information. After that, click `Apply Changes`.

After the changes are updated, there will be a new button `Sync CC policy`. Click on that button and wait for it to finish. After this, you are ready to click the `Run` button on the confidential model.
Make sure you only click on the confidential model's button, don't clikc `Run all`. Inference and metrics calcualtion will take time, so only run the relevant model.
