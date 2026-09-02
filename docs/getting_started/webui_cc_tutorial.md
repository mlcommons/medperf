# Confidential Federated Evaluation Tutorial (WebUI version)

## Overview

This tutorial simulates the scenario running a confidential model on a dataset in a confidential VM. There are three roles that you will play in this tutorial:

- Benchmark owner: an entity that will define the benchmark by implementing a data preparation container, an inference container, and a metrics container. A dataset participating in the benchmark will run these three stages sequentially: data preparation, then inference, and finally metrics calculation. The inference will happen on the cloud in a confidential VM, while the data preparation and the metrics will happen on-prem. The inference container will take as an input the data owner's dataset and the model owner's model weights.

- Model owner: an entity that owns sensitive pretrained model weights and wishes to benchmark them.
- Data owner: an entity that owns senstitive clinical dataset and wishes to run a benchmark on it.

In addition to these roles, you will play the role of the data owner's organization cloud admin and the model owner's organization cloud admin, since you will be setting up the necessary google cloud resources. **Note that running this tutorial requires you to use google cloud with billing enabled, so this will cost some money.**

## Google Cloud Setup

We assume that you already have a google cloud account, you have set up a google cloud project, and you have full privileges on the project. We recommend that you use a separate new project for this tutorial, so that cleanup can be easy (i.e., deleting the resources at the end). You will be playing the two roles of being a GCP admin for the model owner and also the GCP admin for the data owner. You can use the same GCP project ID for both in this tutorial, or you can use two separate projects; it is up to you. However, if you choose to not use the same project, you will need to alternate between projects throughout the tutorial. So it is recommended to use one project for simplicity.

### Create the Model Owner Resources

You will now play the role of the model owner cloud administrator.

1. Read [this file](https://github.com/mlcommons/medperf/tree/main/examples/cc/admin_scripts/README_model_admin.md) to understand what you will be creating.
2. Edit [this script](https://github.com/mlcommons/medperf/tree/main/examples/cc/admin_scripts/model_admin.sh) to fill its configuration variables with correct information.
3. Open a cloud shell in your google cloud console and run the edited script.
4. The script will print at the end some configuration variables summary. Save these somewhere; you will be using them in a later step.

### Create the Data Owner Resources

You will now play the role of the data owner cloud administrator.

1. Read [this file](https://github.com/mlcommons/medperf/tree/main/examples/cc/admin_scripts/README_data_admin.md) to understand what you will be creating.
2. Edit [this script](https://github.com/mlcommons/medperf/tree/main/examples/cc/admin_scripts/data_admin_cpu.sh) to fill its configuration variables with correct information.
3. Open a cloud shell in your google cloud console and run the edited script.
4. The script will print at the end some configuration variables summary. Save these somewhere; you will be using them in a later step.

**Make sure you don't use the same resources you used for the model owner.**

### Install google cloud CLI on your machine

1. Install the gcloud CLI (<https://docs.cloud.google.com/sdk/docs/install-sdk#latest-version>). Follow only the two sections about installing the CLI and initializing google cloud.
2. Run `gcloud auth list` and make sure your account is active (an asterisk should be next to your account email)
3. Set the project ID by running the command `gcloud config set project PROJECT_ID` where `PROJECT_ID` is the project ID you got from your cloud admin.
4. Run the following command `gcloud auth application-default login` and follow the required steps.

**Note that if you chose to use two separate projects for this tutorial, you will need to run steps 3 and 4 again when you switch between the model owner and the data owner users.**

Next, you will be setting up MedPerf.

## MedPerf setup

To start experimenting with MedPerf through this tutorial on your local machine, you need to start by following these quick steps:

  1. **[Install Medperf](../installation)**
  2. **[Set up Medperf](../setup)**

### Prepare the Local MedPerf Server

For the purpose of the tutorial, you have to initialize a local MedPerf server with a fresh database and then create the necessary entities that you will be interacting with. To do so, run the following: (make sure you are in MedPerf's root folder)

```bash
cd server
python -m medperf_server reset_db
python -m medperf_server seed --demo benchmark
cd ..
```

### Download the Necessary files

A script is provided to download all the necessary files so that you follow the tutorial smoothly. Run the following: (make sure you are in MedPerf's root folder)

```bash
sh tutorials_scripts/setup_webui_cc_tutorial.sh
```

This will create a workspace folder `medperf_tutorial` where all necessary files are downloaded.

### Run Medperf WebUI Local client

In your terminal, run the following command to start the local webUI:

```bash
medperf_webui
```

You will see a long URL in the terminal. Click on the URL (CTRL + Click) to open the web UI in the browser.

### Configure the client

Navigate to the settings page and change the `profile` to `local`. This way, the client will communicate with the local MedPerf server for tutorial's sake rather than the real MedPerf server.

## About the tutorial

### Outline

1. Benchmark Owner: Register the benchmark components, then register the benchmark.
2. Model Owner: Register a model (weights).
3. Model Owner: Request participation in the benchmark.
4. Data Owner: Get and submit a certificate.
5. Data Owner: Register a dataset, prepare it, and set it operational.
6. Data Owner: Request participation.
7. Benchmark Owner: Approve the participation requests.
8. Model Owner: Configure the model for confidential computing.
9. Data Owner: Configure the dataset for confidential computing.
10. Data Owner: Set up the confidential computing operator.
11. Data Owner: Run the benchmark and submit the results.
12. Benchmark Owner: View the results.

The tutorial components are located in your workspace under `medperf_tutorial`:

```txt
medperf_tutorial/
├── data_preparator/                          # Data preparation container
├── cc_chestxray/                             # Confidential VM inference container
├── metrics/                                  # Metrics container (scores predictions locally)
├── sample_raw_data/                          # Raw chest X-ray data (images + labels)
└── cnn_weights.tar.gz                        # Model owner's weights tarball
```

### Benchmark script

The benchmark inference container is the script that runs inside the confidential VM. As a benchmark owner, you build it from a template so that it conforms to the interface MedPerf expects (it receives the input data, the input labels, and the model files, and writes its output to a results directory).

For this tutorial you do not need to build anything. A ready-made implementation is provided at `medperf_tutorial/cc_chestxray` and is what will be used in the walkthrough below.

## 1. Benchmark Owner: Register the containers and the benchmark

First, login as the benchmark owner:

- Navigate to the `Login` page and use the email `testbo@example.com`.

### Defining the benchmark components

The benchmark is built from three components:

- **Data Preparator Container:** Transforms raw data into a format ready to be ingested by the model. In this tutorial it turns chest X-ray images and labels into numpy arrays. Its implementation is in `medperf_tutorial/data_preparator`.

- **Reference Model Inference Container:** The container that runs inside the confidential VM. It loads model weights, runs inference on the data, and outputs predictions. This is the container implemented in `medperf_tutorial/cc_chestxray`.

- **Metrics Container:** An evaluator container that runs locally to score the predictions produced by the VM against the ground-truth labels (computing Accuracy and AUC). Its implementation is in `medperf_tutorial/metrics`.

### Register the Data Preparator Container

Navigate to the `Containers` tab at the top, and click on the `Register a New Container` button.

For the Data Preparator container, fill in:

- A container name, e.g. `cc-prep`.
- The path to the container configuration file (type it or use `Browse`):

    ```
    medperf_tutorial/data_preparator/container_config.yaml
    ```

- The path to the parameters file:

    ```
    medperf_tutorial/data_preparator/workspace/parameters.yaml
    ```

Leave `Additional Files URL` empty, keep `Not Encrypted` selected, and click `Register container`.

### Register the Reference Model Inference Container

The reference model inference container is the inference script that will run inside the confidential VM.

Navigate to the `Containers` tab at the top, and click on the `Register a New Container` button.

Fill in:

- A container name, e.g. `cc-inference-script`.
- The path to the container configuration file:

    ```
    medperf_tutorial/cc_chestxray/container_config_modelonly.yaml
    ```

Leave `Parameters File` empty, `Additional Files URL` empty, keep `Not Encrypted` selected, and click `Register container`.

### Register the Metrics Container

Navigate back to the `Containers` tab, and click on the `Register a New Container` button.

For the metrics container, fill in:

- A container name, e.g. `cc-metrics`.
- The path to the container configuration file:

    ```
    medperf_tutorial/metrics/container_config.yaml
    ```

- The path to the parameters file:

    ```
    medperf_tutorial/metrics/workspace/parameters.yaml
    ```

Leave `Additional Files URL` empty, keep `Not Encrypted` selected, and click `Register container`.

### Register the benchmark

Navigate to the `Benchmarks` tab at the top, and click on the `Register Benchmark` button.

Fill in the form:

- Select `Skip Compatibility Tests`.
- **Benchmark Name**: e.g. `cc-bmk`.
- **Description**: e.g. `CC benchmark test`.
- **Data Preparation Container**: select `cc-prep` from the dropdown.
- **Reference Model**: select `cc-inference-script` from the dropdown.
- **Metrics Container**: select `cc-metrics` from the dropdown.

Click `Register Benchmark`.

## 2. Model Owner: Register a model

- Logout (via the user icon at the top right), then login with the email `testmo@example.com` to login as the model owner.

As the model owner, you contribute a confidential model as a set of **weights** registered as an asset. These weights are loaded into the benchmark's inference script container when it runs inside the confidential VM. In this tutorial, the weights tarball is available locally in your workspace at `medperf_tutorial/cnn_weights.tar.gz`.

### Register your model

Navigate to the `Models` tab at the top, and click on the `Register a New Asset Model` button.

Fill in:

- An asset name, e.g. `cc-mobilenet-weights`.
- Select `Local Asset`.
- In the `Asset Path` field, enter (or `Browse` to) the path to your weights tarball:

    ```
    medperf_tutorial/cnn_weights.tar.gz
    ```

Click `Register`.

## 3. Model Owner: Request participation in the benchmark

You must request to associate your model with the benchmark in order to be part of it.

Navigate to the `Models` tab, open your model's detail page (`cc-mobilenet-weights`), and click on the `Associate with Benchmark` button. In the dropdown, find the target benchmark (`cc-bmk`) and click `Request`.

!!! note
    The benchmark owner will need to approve this request (in step 8) before your model can be run.

## 4. Data Owner: Get and submit a certificate

- Logout, then login with the email `testdo@example.com` to login as the data owner.

Confidential computing uses a certificate to identify you and to secure the predictions the confidential VM produces for you. The VM encrypts the predictions with your public key, and only you can decrypt them with your private key. You only need to do this once.

1. Navigate to the `Settings` page by clicking on the user icon at the top right.
2. Scroll down to the `Certificate Settings` section.
3. Click `Get User Certificate` and follow the prompts. The status will change to `to be uploaded`.
4. Click `Submit Certificate` to upload it to the MedPerf server.

## 5. Data Owner: Register a dataset

Navigate to the `Datasets` tab at the top, and click on the `Register a New Dataset` button.

You will be registering the dataset located at `medperf_tutorial/sample_raw_data`. Fill in:

- **Select Benchmark**: choose the benchmark you want to participate in (`cc-bmk`). This ensures your data will be prepared using the benchmark's data preparation container.
- **Dataset Name**: e.g. `cc_dataset_a`.
- **Description**: e.g. `CC mock dataset a`.
- **Location**: e.g. `mock-location-a` (for example, a hospital name).
- **Data Folder**: the path to the data records:

    ```
    medperf_tutorial/sample_raw_data/images
    ```

- **Labels Folder**: the path to the labels:

    ```
    medperf_tutorial/sample_raw_data/labels
    ```

Leave `Submit as Prepared` off, then click `Register Dataset`.

!!! note
    You will be submitting general information about the data, not the data itself.

## 6. Data Owner: Run data preparation and set operational

Open your dataset's detail page. In the `Actions` section:

1. Click the `Prepare` button. This runs data preprocessing and sanity checks locally.
2. Once preparation completes, click the `Set operational` button to mark your dataset as ready for benchmarking. This also uploads some statistics calculated on the dataset according to the benchmark owner's requirement (here, the number of cases and the label counts).

## 7. Data Owner: Request participation

Still on your dataset's detail page, in the `Actions` section, click the `Associate with benchmark` button. In the dropdown, find `cc-bmk` and click `Request`.

You won't be able to run the benchmark until the benchmark owner approves your association request.

## 8. Benchmark Owner: Approve the participation requests

Logout, then login as the benchmark owner (`testbo@example.com`). Navigate to your benchmark's detail page (`cc-bmk`).

- Expand the `Datasets Associations` panel and approve the request from the data owner.
- Expand the `Models Associations` panel and approve the request from the model owner.

## 9. Model Owner: Configure the model for confidential computing

Logout, then login as the model owner (`testmo@example.com`). Open your model's detail page (`cc-mobilenet-weights`) and scroll down to the `Confidential Computing Preferences` section.

1. Turn on the `Configure model for Confidential Computing` toggle.
2. Fill in the cloud environment information your cloud administrator gave you (the values produced by `model_admin.sh` in the setup section. The ones below are just examples.):

    | Field | Example value |
    | --- | --- |
    | GCP Project ID | `proj30914` |
    | GCP Project Number | `819939352708` |
    | GCP Bucket Name | `model-owner-bucket-medperf` |
    | GCP KMS Keyring Name | `model-owner-keyring` |
    | GCP KMS Key Name | `model-owner-key` |
    | GCP KMS Key Location | `us-west1` |
    | GCP Workload Identity Pool Name | `model-owner-wip` |
    | GCP Workload Identity Pool Provider | `attestation-verifier` |

3. Click `Configure`.
4. A `Sync CC policy` button will appear. Click it to publish your model's confidential computing policy to the server.

!!! note
    This step encrypts the model weights, uploads them to your cloud resources, and defines the policy that the confidential VM must satisfy before the weights can be decrypted.

## 10. Data Owner: Configure the dataset for confidential computing

Logout, then login as the data owner (`testdo@example.com`). Open your dataset's detail page (`cc_dataset_a`) and scroll down to the `Confidential Computing Preferences` section.

1. Turn on the `Configure dataset for Confidential Computing` toggle.
2. Fill in the cloud environment information your cloud administrator gave you ( part of the values produced by `data_admin_cpu.sh` in the setup section. The ones below are just examples.):

    | Field | Example value |
    | --- | --- |
    | GCP Project ID | `proj30914` |
    | GCP Project Number | `819939352708` |
    | GCP Bucket Name | `data-owner-bucket-medperf-cc` |
    | GCP KMS Keyring Name | `data-owner-keyring` |
    | GCP KMS Key Name | `data-owner-key2` |
    | GCP KMS Key Location | `us-west1` |
    | GCP Workload Identity Pool Name | `data-owner-wip` |
    | GCP Workload Identity Pool Provider | `attestation-verifier` |

3. Click `Configure`.
4. Click the `Sync CC policy` button that appears.

!!! note
    This step encrypts the data, uploads them to your cloud resources, and defines the policy that the confidential VM must satisfy before the data can be decrypted.

## 11. Data Owner: Set up the confidential computing operator

The data owner also acts as the **operator** who owns the confidential VM where the execution runs.

1. Navigate to the `Settings` page (user icon at the top right).
2. Scroll down to the `Confidential Computing Operator Settings` section.
3. Turn on the `Configure Confidential Computing` toggle.
4. Fill in the operator information your cloud administrator gave you (Part of the values produced by `data_admin_cpu.sh` in the setup section. The ones below are just examples.):

    | Field | Example value |
    | --- | --- |
    | GCP Project ID | `proj30914` |
    | GCP Service Account Name | `cc-workload-operator` |
    | GCP Bucket Name | `data-owner-bucket-medperf-cc` |
    | VM Zone | `us-west1-b` |
    | VM Name | `testvm` |

5. Click `Configure`.

## 12. Data Owner: Run the benchmark

Navigate to the `Datasets` tab and open your dataset's detail page (`cc_dataset_a`). Scroll down to the section for the approved benchmark (`cc-bmk`), where the associated models are listed.

Each confidential model shows a `Confidential Computing Model` label together with a `Ready` / `Not Ready` status. After completing steps 9–11, the model should be `Ready`.

Click the `Run` button next to a model to launch the confidential execution. Behind the scenes, MedPerf:

1. Starts the confidential VM, which attests itself and, if the policies are satisfied, is allowed to decrypt the model weights and your data.
2. Runs the reference inference container inside the VM to produce **predictions**.
3. Encrypts the predictions with your public key and uploads them; your machine downloads and decrypts them.
4. Runs the `cc-metrics` container **locally** to score the predictions and produce the metrics.

!!! note
    If a model shows `Not Ready`, hover over the status to see what is missing (for example, the model's or dataset's CC policy has not been synced yet, or the operator is not configured).

## 13. Data Owner: Submit the results

Once an execution finishes, a `View Result` button appears so you can inspect the metrics locally. When you are ready to share them, click the `Submit` button next to the model to upload the result to the MedPerf server, so that the benchmark owner can view it.

## 14. Benchmark Owner: View the results

Logout, then login as the benchmark owner (`testbo@example.com`). Navigate to your benchmark's detail page (`cc-bmk`) and expand the `Results` panel to see the submitted results.

## 15. Cleanup resources

**Make sure you delete all resources you created on google cloud to avoid additional costs.**

**This concludes our tutorial!**
