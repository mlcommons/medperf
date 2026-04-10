# Federated Training with Flower

You will be using MedPerf to run a federated learning experiment for the task of chest X-ray classification using the [Flower Framework](https://flower.ai/).
The data used for this tutorial is a sample from the [NIH Chest-Xray dataset](https://nihcc.app.box.com/v/ChestXray-NIHCC)

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
14. Data Owner 1: Stop the Training Node
15. Data Owner 2: Stop the Training Node

## Running in cloud via Github Codespaces

As the easiest way to play with the tutorials you can launch a preinstalled [Codespace](https://github.com/features/codespaces) cloud environment for MedPerf by clicking this link:

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/mlcommons/medperf/tree/flwr-integration?devcontainer_path=.devcontainer%2Fwebui_training%2Fdevcontainer.json){target="\_blank"}

After opening the link, proceed to creating the codespace without changing any option. It will take around 7 minutes to get the codespace up and running. Please wait until you see the message `Medperf is ready for local usage` printed on the terminal.

Once the codespace is ready, you will get three URLs. Each URL corresponds to the MedPerf webUI instance for a user role (Model Owner, data1 owner, and data2 owner). Make sure you use the correct webUI instance for each tutorial section.

Additionally, you will get the address that you will later use in the tutorial when you register the aggregator server.

Now, we can start the tutorial.

## 1. Model Owner: Register the Data Preparation Container

Make sure you use the `Model Owner` webUI instance.

Make sure you click in the `Training` button on the top of the web page. This will switch MedPerf mode to Training.

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

The training container represents the Flower container. It contains the training logic that will run on each collaborator's machine and also the aggregator server logic. You can take a look at the implementation in the following folder: `medperf_tutorial/fl_container`.

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

Navigate to the `Experiments` tab at the top, and click on the `Register a new training experiment` button.

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
- The network address (hostname or IP) of the machine where the aggregator will run. For the tutorial, this information was given when you opened the codespace.
- The port for federated learning communication (e.g., `50273`).
- The admin port for management commands (e.g., `50274`).
- The name of the **training container** registered in step 2 (e.g., `train-chestxray`).

## 5. Model Owner: Set the Aggregator on the Training Experiment

Navigate to the `Experiments` tab and open your training experiment's detail page. Click the `Set Aggregator` button and select the aggregator registered in step 4 (e.g., `aggreg`).

## 6. Model Owner: Submit the Training Plan

On your training experiment's detail page, click the `Set Plan` button.

The training plan is a configuration file that defines the federated learning hyperparameters (e.g., number of rounds, aggregation strategy). Provide the path to the plan file:

```
medperf_tutorial/fl_container/workspace/training_config.yaml
```

## 7. Model Owner: Start the Training Event

On your training experiment's detail page, click the `Start Event` button.

To start the training event, you need to provide:

- A name for the event (e.g., `event1`).
- The list of collaborator emails who will participate in this event. For this tutorial, use the file located at `medperf_tutorial/cols_list.yaml`, which contains the emails of the two data owners used in this tutorial.

## 8. Data Owner 1: Register, prepare, and associate their dataset

Make sure you use the `Data Owner 1` webUI instance.

Make sure you click in the `Training` button on the top of the web page. This will switch MedPerf mode to Training.

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

Make sure you use the `Data Owner 2` webUI instance.

Make sure you click in the `Training` button on the top of the web page. This will switch MedPerf mode to Training.

Follow the same steps as Data Owner 1 (steps 8 and 9) using the second dataset:

- Dataset name: `col2`
- Path to data records: `medperf_tutorial/sample_raw_data/col2/images`
- Path to labels: `medperf_tutorial/sample_raw_data/col2/labels`

## 11. Data Owner 2: Get and submit a client certificate, then start training

Follow the same certificate and training steps as Data Owner 1:

1. On the settings page, click `Get User Certificate` to generate a certificate locally.
2. On the settings page, click `Submit Certificate` to upload it to the MedPerf server.
3. On the dataset dashboard, Click `Start Training` next to the training experiment (`trainexp`).

The second training client will now also be running a federated node in the background.

## 12. Model Owner: Get the server certificate and start the aggregator

Make sure you use the `Model Owner` webUI instance.

### Get the server certificate

Navigate to the `Aggregators` tab and open your aggregator's detail page. Click the `Get Certificate` button to generate the server-side TLS certificate used by the aggregator.

### Start the aggregator

In the `Run aggregator` section, select the training experiment (e.g., `trainexp`) and the network interface you want the server to bind to. For the tutorial, use `0.0.0.0` (which will listen on all interfaces). Then, click the `Run aggregator` button.

The aggregator will start on your machine, and the collaborators' training clients (from steps 9 and 11) will automatically connect to it.

## 13. Model Owner: Close the Training Event

Once the aggregator has finished, navigate to your training experiment's detail page and click the `Close Event` button to finalize the training event.

## 14. Data Owner 1: Stop the Training Node

You can open the `Data Owner 1` webUI instance and click the `Stop` button to stop the training node.

## 15. Data Owner 2: Stop the Training Node

You can open the `Data Owner 2` webUI instance and click the `Stop` button to stop the training node.

**This concludes our tutorial!**
