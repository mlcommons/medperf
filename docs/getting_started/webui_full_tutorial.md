# Federated Evaluation Tutorial (WebUI version)

## Requirements

To run this tutorial, you need a machine with the following requirements:

- Internet access.
- Web browser (to connect to codespaces)

## Running in cloud via Github Codespaces

As the most easy way to play with the tutorials you can launch a preinstalled [Codespace](https://github.com/features/codespaces) cloud environment for MedPerf by clicking this link:

<!-- [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=416800365&devcontainer_path=.devcontainer%2Fwebui%2Fdevcontainer.json) -->
[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?hide_repo_select=true&ref=webui-doc&repo=895759437&devcontainer_path=.devcontainer%2Fwebui%2Fdevcontainer.json)

After opening the link, proceed to creating the codespace without changing options. It will take around 7 minutes to get the codespace up and running. Please wait until you see the message `Medperf is ready for local usage` printed on the terminal.

## Run Medperf WebUI Local Server

In your codespaces terminal, run the following command to start the local webUI:

```bash
medperf_webui
```

You will see a long URL in the terminal. Click on the URL (CTRL + Click) to open the web UI in the browser.

## About the tutorial

You will be using MedPerf to do federated benchmarking for the task of chest X-ray classification. The data consists of chest X-ray images and their labels. You can take a look at the data located in this folder: `medperf_tutorial/sample_raw_data`.

Througout the tutorial, you will play three roles:

- The benchmark owner who defines and manages the benchmarking experiment.
- The model owner who will provide a model to be benchmarked.
- The data owner who will provide their data for benchmarking the model. (Note that the data stays on the data owner machine)

The following outlines the steps involved:

1. Benchmark Owner: Define and register the benchmark.
2. Model Owner: Register a model
3. Model Owner: Request participation in the benchmark
4. Data Owner: Register a dataset
5. Data Owner: Data Owner: Run data preparation.
6. Data Owner: Request participation
7. Benchmark Owner: Approve the participation requests
8. Data Owner: Run the benchmark
9. Data Owner: Submit the results
10. Benchmark Owner: View the results.

## 1. Benchmark Owner: Define and register the benchmark

First, login as the benchmark owner.

- Use the email `testbo@example.com`.

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/login_bmk_owner.mp4" width="800px" controls></video>

### Defining the benchmark Components

The implementation of a valid benchmark workflow is accomplished by implementing three Containers:

- **Data Preparator Container:** This container transforms raw data into a format ready to be ingested by AI models. In this tutorial, the data preparation container will transform chest x-ray images and labels into numpy arrays. You can take a look at the implementation in the following folder: `medperf_tutorial/data_preparator`.

- **Reference Model Container:** Provides an example AI model compatible with the benchmark, so that models respect the input data format and write predictions in a format specified by the benchmark owner. For this tutorial, you can take a look at the implementation in the following folder: `medperf_tutorial/model_custom_cnn`.

- **Metrics Container:** Evaluates model performance by comparing models predictions to the data ground truth labels. For this tutorial, the metrics container will calculate Accuracy and AUC metrics. You can take a look at the implementation in the following folder: `medperf_tutorial/metrics`.

Additionally, a demo/toy dataset should be provided as part of the benchmark to be used for testing the compatibility and validity of participating models.

All these four components are already ready to be used for this tutorial. Below, you will learn how to register them to the MedPerf server and then register the benchmark.

### Register the three Containers

#### Data Preparator Container

In this tutorial, for the Data Preparator container, the registration should include:

- The URL to the hosted container configuration file, which is:

    ```
    https://raw.githubusercontent.com/mlcommons/medperf/main/examples/chestxray_tutorial/data_preparator/container_config.yaml
    ```

- The URL to the hosted parameters file, which is:

    ```
    https://raw.githubusercontent.com/mlcommons/medperf/main/examples/chestxray_tutorial/data_preparator/workspace/parameters.yaml
    ```

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/register_data_prep.mp4" width="800px" controls></video>

#### Reference Model Container

In this tutorial, for the Reference Model container, the registration should include:

- The URL to the hosted container configuration file:

    ```
    https://raw.githubusercontent.com/mlcommons/medperf/main/examples/chestxray_tutorial/model_custom_cnn/container_config.yaml
    ```

- The URL to the hosted parameters file:

    ```
    https://raw.githubusercontent.com/mlcommons/medperf/main/examples/chestxray_tutorial/model_custom_cnn/workspace/parameters.yaml
    ```

- The URL to the hosted additional files tarball file, which includes model weights:

    ```
    https://storage.googleapis.com/medperf-storage/chestxray_tutorial/cnn_weights.tar.gz
    ```

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/register_reference_model.mp4" width="800px" controls></video>

#### Metrics Container

In this tutorial, for the Metrics container, the registration should include:

- The URL to the hosted container configuration file:

    ```
    https://raw.githubusercontent.com/mlcommons/medperf/main/examples/chestxray_tutorial/metrics/container_config.yaml
    ```

- The URL to the hosted parameters file:

    ```
    https://raw.githubusercontent.com/mlcommons/medperf/main/examples/chestxray_tutorial/metrics/workspace/parameters.yaml
    ```

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/register_evaluator.mp4" width="800px" controls></video>

> Finally, now after having the containers registered, you can register the benchmark to the MedPerf server.

### Register the benchmark

You need to keep at hand the following information:

- The Demo/Toy Dataset URL. Here, the URL will be:

    ```
    https://storage.googleapis.com/medperf-storage/chestxray_tutorial/demo_data.tar.gz
    ```

> The names you used for the three containers that you have registered in the previous steps.

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/bmk_register.mp4" width="800px" controls></video>

## 2. Model Owner: Register a model

- Use the email `testmo@example.com` to login as the Model Owner.

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/login_model_owner.mp4" width="800px" controls></video>

The implementation of the model container that will we will be registering in this section can be found in the following folder: `medperf_tutorial/model_mobilenetv2`.

### Register your model

In this tutorial, for the model owner's container, the registration should include:

- The URL to the hosted container configuration file:

    ```
    https://raw.githubusercontent.com/mlcommons/medperf/main/examples/chestxray_tutorial/model_mobilenetv2/container_config.yaml
    ```

- The URL to the hosted parameters file:

    ```
    https://raw.githubusercontent.com/mlcommons/medperf/main/examples/chestxray_tutorial/model_mobilenetv2/workspace/parameters.yaml
    ```

- The URL to the hosted additional files tarball file (which contains the model weights):

    ```
    https://storage.googleapis.com/medperf-storage/chestxray_tutorial/mobilenetv2_weights.tar.gz
    ```

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/model_register.mp4" width="800px" controls></video>

## 3. Model Owner: Request participation in the benchmark

Benchmark workflows are run by Data Owners, who will get notified when a new model is added to a benchmark. You must request to associate your model in order to be part of the benchmark.

To initiate an association request, you need to remember the following information:

- The target benchmark name.
- Your container's name.

> Then visit your container's detail page, and start the association request.

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/model_request_association.mp4" width="800px" controls></video>

## 4. Data Owner: Register a dataset

- Use the email `testdo@example.com` to login as Dataset Owner.

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/login_dataset_owner.mp4" width="800px" controls></video>

### Register your dataset

You will be registering the dataset located at `medperf_tutorial/sample_raw_data`.

To register your dataset, you need to collect the following information:

- A name you wish to have for your dataset.
- A small description of the dataset.
- The source location of your data (e.g., hospital name).
- The path to the data records (here, it is `medperf_tutorial/sample_raw_data/images`).
- The path to the labels of the data (here, it is `medperf_tutorial/sample_raw_data/labels`)
- The benchmark that you wish to participate in. This ensures your data in the next step will be prepared using the benchmark's data preparation container.

> Note: You will be submitting general information about the data, not the data itself. The data never leaves your machine.

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/dataset_register.mp4" width="800px" controls></video>

## 5. Data Owner: Run data preparation

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/dataset_prepare.mp4" width="800px" controls></video>

### Set dataset into operational mode

After running preparation, click on `set opertional` to mark your dataset as ready for benchmarking. This will also upload some statistics calculated on the dataset according to the benchmark owner's requirement.

# TODO: mention statistics

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/dataset_set_operational.mp4" width="800px" controls></video>

## 6. Data Owner: Request participation

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/dataset_request_association.mp4" width="800px" controls></video>

## 7. Benchmark Owner: Approve the participation requests

Login as Benchmark Owner then accept participation requests from the model owner and from the data owner.

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/bmk_approve_associations.mp4" width="800px" controls></video>

## 8. Data Owner: Run the benchmark

Now, login as the data owner, navigate to your dataset page, and run the benchmark on your data:

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/run_execution.mp4" width="800px" controls></video>

### Data Owner: Submit the results

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/view_and_submit_results.mp4" width="800px" controls></video>

## 10. Benchmark Owner: View the results

Now, login as the benchmark owner, navigate to your benchmark page, and you can see the results.

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/bmk_view_results.mp4" width="800px" controls></video>

This concludes our tutorial!
