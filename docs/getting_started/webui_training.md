# Federated Training with Flower

You will be using MedPerf to run a federated learning experiment for the task of chest X-ray classification using the [Flower Framework](https://flower.ai/).

Throughout the tutorial, you will play three roles:

- The **Model owner** who defines and manages the federated learning experiment, and also runs the aggregation server.
- **Data Owner 1** and **Data Owner 2**, who are collaborators providing their local data for training. The data never leaves their machines.

The following outlines the steps involved:

1. Model Owner: Register the Data Preparation Container
2. Model Owner: Submit the Flower container
3. Model Owner: Create a Training Experiment
4. Model Owner: Submit the Aggregator
5. Model Owner: Link the Aggregator to the Training Experiment
6. Model Owner: Submit the Training Plan (Configuration)
7. Model Owner: Start the Training Event
8. Data Owner 1: Register, prepare, and associate their dataset
9. Data Owner 1: Get and submit a signing certificate, then start training
10. Data Owner 2: Register, prepare, and associate their dataset
11. Data Owner 2: Get and submit a signing certificate, then start training
12. Model Owner: Get a server certificate and start the aggregator
13. Model Owner: Close the Training Event

## Setup

To run this tutorial, you need to:

- Follow the MedPerf installation [instructions here](../getting_started/installation.md)
- Follow the Setup [instructions here](../getting_started/setup.md). Note that this tutorial only works with Docker.
- Navigate to the `server` folder and run the following command to seed the database with necessary records:

```bash
python seed.py --demo benchmark
```

- In a new terminal, navigate to the root folder of the MedPerf repository and run the following command to setup/download required assets for the tutorial:

```bash
bash tutorial_scripts/setup_webui_training_tutorial.sh
```

## Run Local Medperf WebUI

The MedPerf WebUI is a local web application.

Run the following command to start the local WebUI instances. Make sure you are in the MedPerf repository root folder:

```bash
medperf_webui --port 8001
```

You will see a long URL in the terminal. Copy the link and open it in the browser.

Now, we can start the tutorial.

## 1. Model Owner: Register the Data Preparation Container

First, login as the model owner.

- Use the email `testmo@example.com`.

The data preparation container transforms raw data into a format ready for training. In this tutorial, it will transform chest X-ray images and labels into numpy arrays. You can take a look at the implementation in the following folder: `medperf_tutorial/data_preparator`.

Navigate to the `Containers` tab at the top, and click on the `Register a new container` button.

For the Data Preparation container, the registration should include:

- The path to the container configuration file:

    ```
    medperf_tutorial/data_preparator/container_config.yaml
    ```

- The path to the parameters file:

    ```
    medperf_tutorial/data_preparator/workspace/parameters.yaml
    ```

Give this container a memorable name (e.g., `chestxray_prep`).

## 2. Model Owner: Submit containers

The training container represents the Flower container. It contains the training logic that will run on each collaborator's machine and also the aggregator server logic.

Navigate to the `Containers` tab at the top, and click on the `Register a new container` button.

For the training container, the registration should include:

- The path to the container configuration file:

    ```
    medperf_tutorial/fl_container/container_config.yaml
    ```

- The URL to the hosted additional files tarball file, which includes the initial model weights:

    ```
    https://storage.googleapis.com/medperf-storage/init_weights_flower.tar.gz
    ```

Give this container a memorable name (e.g., `train-chestxray`).

## 3. Model Owner: Create a Training Experiment

Navigate to the `Training` tab at the top, and click on the `Register a new training experiment` button.

To register the training experiment, you need the following information:

- A name for the experiment (e.g., `trainexp`).
- A short description.
- The name of the **data preparator container** you registered in step 1 (e.g., `chestxray_prep`).
- The name of the **training container** you registered in step 2 (e.g., `train-chestxray`).

After submitting, the training experiment will be reviewed and approved by the MedPerf administrator before proceeding. For the tutorial, it will be auto approved, so that you can proceed.

## 4. Model Owner: Submit the Aggregator

Navigate to the `Aggregators` tab at the top, and click on the `Register a new aggregator` button.

To register the aggregator, you need the following information:

- A name for the aggregator (e.g., `aggreg`).
- The network address (hostname or IP) of the machine where the aggregator will run.
- The port for federated learning communication (e.g., `50273`).
- The admin port for management commands (e.g., `50274`).
- The name of the **training container** registered in step 2 (e.g., `train-chestxray`).

## 5. Model Owner: Set the Aggregator on the Training Experiment

Navigate to the `Training` tab and open your training experiment's detail page. Click the `Set Aggregator` button and select the aggregator registered in step 4 (e.g., `aggreg`).

## 6. Model Owner: Submit the Training Plan

On your training experiment's detail page, click the `Set Plan` button.

The training plan is a configuration file that defines the federated learning hyperparameters (e.g., number of rounds, aggregation strategy). Provide the path to the plan file:

```
medperf_tutorial/training_config.yaml
```

## 7. Model Owner: Start the Training Event

On your training experiment's detail page, click the `Start Event` button.

To start the training event, you need to provide:

- A name for the event (e.g., `event1`).
- The list of collaborator emails who will participate in this event. For this tutorial, use the file located at `medperf_tutorial/cols_list.yaml`, which contains the emails of the two data owners used in this tutorial.

## 8. Data Owner 1: Register, prepare, and associate their dataset

Logout, then login as the first data owner.

- Use the email `testdo@example.com`.

### Register the dataset

Navigate to the `Datasets` tab at the top, and click on the `Register a new dataset` button.

To register the dataset, you need the following information:

- A name (e.g., `col1`).
- A short description.
- The source location of the data (e.g., `col1location`).
- The path to the data records: `medperf_tutorial/sample_raw_data/col1/images`.
- The path to the labels: `medperf_tutorial/sample_raw_data/col1/labels`.
- The **data preparator container** name: `chestxray_prep`.

The data consists of chest X-ray images and their labels. You can take a look at the data located in this folder: `medperf_tutorial/sample_raw_data`.

!!! note
    You will be submitting general information about the data, not the data itself. The data never leaves your machine.

### Prepare the dataset

On your dataset's detail page, click the `Prepare` button to run the data preparation container on your local data.

### Set the dataset to operational mode

After preparation completes, click the `Set Operational` button to mark your dataset as ready for training. This will also upload dataset statistics to the MedPerf server.

### Associate with the training experiment

Click the `Associate with a training experiment` button on your dataset's detail page, and select the training experiment created in step 3 (e.g., `trainexp`).

## 9. Data Owner 1: Get and submit a client certificate, then start training

Still logged in as Data Owner 1, navigate to the settings page, and scroll down to the signing certificate section.

### Get and submit a client certificate

Before starting training, you need a client certificate so the aggregator can authenticate you.

Click the `Get User Certificate` button to generate a certificate on your local machine.

Then click the `Submit Certificate` button to upload your public certificate to the MedPerf server.

### Start training

Navigate to your dataset dashboard, scroll down to the training experiments section.
Click the `Start Training` button next to the training experiment (e.g., `trainexp`).

The training node will start in the background on your machine.

## 10. Data Owner 2: Register, prepare, and associate their dataset

For the tutorial purposes, you will need to run another instance of the web UI. Leave the current web UI instance running.

Open a new terminal, navigate to the medperf repository folder, and run the following command to create another web UI instance:

```bash
medperf_webui --port 8002
```

Logout, then login as the second data owner.

- Use the email `testdo2@example.com`.

Follow the same steps as Data Owner 1 (steps 8 and 9) using the second dataset:

- Dataset name: `col2`
- Path to data records: `medperf_tutorial/sample_raw_data/col2/images`
- Path to labels: `medperf_tutorial/sample_raw_data/col2/labels`

## 11. Data Owner 2: Get and submit a client certificate, then start training

Still logged in as Data Owner 2, follow the same certificate and training steps as Data Owner 1:

1. On the settings page, click `Get User Certificate` to generate a certificate locally.
2. On the settings page, click `Submit Certificate` to upload it to the MedPerf server.
3. On the dataset dashboard, Click `Start Training` next to the training experiment (`trainexp`).

The second training client will now also be running a federated node in the background.

## 12. Model Owner: Get the server certificate and start the aggregator

For the tutorial purposes, you will need to run another instance of the web UI. Leave the current two web UI instances running.

Open a new terminal, navigate to the medperf repository folder, and run the following command to create another web UI instance:

```bash
medperf_webui --port 8003
```

Logout, then login as the model owner (`testmo@example.com`).

### Get the server certificate

Navigate to the `Aggregators` tab and open your aggregator's detail page. Click the `Get Certificate` button to generate the server-side TLS certificate used by the aggregator.

### Start the aggregator

In the `Run aggregator` section, select the training experiment (e.g., `trainexp`) and the network interface you want the server to bind to. For the tutorial, you may use the the local network interface (not localhost), or just `0.0.0.0` (which will listen on all interfaces). Then, click the `Run aggregator` button.

The aggregator will start on your machine, and the collaborators' training clients (from steps 9 and 11) will automatically connect to it.

## 13. Model Owner: Close the Training Event

Once the aggregator has finished, navigate to your training experiment's detail page and click the `Close Event` button to finalize the training event.

**This concludes our tutorial!**
