# Federated Evaluation Tutorial (WebUI version)

## Requirements

To run this tutorial, you need a machine with the following requirements:

- Internet access.
- Web browser (to connect to codespaces)

## Run Medperf WebUI Local Server

In your codespaces terminal, run the following command to start the local webUI:

```bash
medperf_webui
```

## Inference Setup with MedPerf (Benchmark Owner)

### Implement a Valid Workflow

The implementation of a valid workflow is accomplished by implementing three Containers:

- Data Preparator Container: This Container prepares raw data into MedPerf-compatible datasets for AI model execution.

- Reference Model Container: Provides an example AI model compatible with the data preparation Container.

- Metrics Container: Evaluates model performance using outputs from the reference model Container.

### Develop a Demo Dataset

A demo dataset is a small labeled reference dataset used to test the benchmark workflow in two scenarios:

- It is used to test the benchmark’s default workflow, where the MedPerf client runs automatic compatibility checks of the three containers using the demo dataset.

- When a model owner joins a benchmark, the MedPerf client tests their model’s compatibility with the data preparation and metrics containers using the demo dataset.

With the three containers and demo data ready, you can test the workflow locally, which is recommended before submitting any asset to the MedPerf server.

## Login to the Local MedPerf Server (Benchmark Owner)

- Use the email `testbo@example.com` to login as Benchmark Owner.

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/login_bmk_owner.mp4" width="800px" controls></video>

### Register the Containers

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

- The URL to the hosted additional files tarball file:

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

> Finally, now after having the containers registered and the demo dataset hosted, you can register the benchmark to the MedPerf server.

### Register the benchmark

You need to keep at hand the following information:

- The Demo Dataset URL. Here, the URL will be:

    ```
    https://storage.googleapis.com/medperf-storage/chestxray_tutorial/demo_data.tar.gz
    ```

> The names of the three containers registered can be found in the containers listing page.

For this tutorial, the names are as follows:

- Data preparator Name: `my-prep`
- Reference model Name: `my-refmodel`
- Evaluator Name: `my-metrics`

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/bmk_register.mp4" width="800px" controls></video>

## Participate as a model owner (Model Owner)

- Use the email `testmo@example.com` to login as Model Owner.

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/login_model_owner.mp4" width="800px" controls></video>

### Run container compatibility test

- To test your container validity with the benchmark, first check the benchmarks listing page to identify the benchmark. In this tutorial, the benchmark name is the one specified while registering the benchmark above: `tutorial bmk`.

- Next, locate the container. Unless you implemented your own container, the container provided for this tutorial is located in your workspace: `medperf_tutorial/model_mobilenetv2/container_config.yaml`.

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/model_compatibility_test.mp4" width="800px" controls></video>

> Assuming the test passes successfully, you are ready to register the model after hosting the container's assets.

### Register your model

The registration should include the URLs of all the hosted assets. For the Container provided for the tutorial:

- The URL to the hosted container configuration file is

    ```
    https://raw.githubusercontent.com/mlcommons/medperf/main/examples/chestxray_tutorial/model_mobilenetv2/container_config.yaml
    ```

- The URL to the hosted parameters file is

    ```
    https://raw.githubusercontent.com/mlcommons/medperf/main/examples/chestxray_tutorial/model_mobilenetv2/workspace/parameters.yaml
    ```

- The URL to the hosted additional files tarball file is

    ```
    https://storage.googleapis.com/medperf-storage/chestxray_tutorial/mobilenetv2_weights.tar.gz
    ```

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/model_register.mp4" width="800px" controls></video>

### Request participation

Benchmark workflows are run by Data Owners, who will get notified when a new model is added to a benchmark. You must request the association for your model to be part of the benchmark.

To initiate an association request, you need to collect the following information:

- The target benchmark.
- Your container's name, UID.

> Then visit your container's detail page, and start the association request.

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/model_request_association.mp4" width="800px" controls></video>

## Participate as a data owner (Inference data Owner)

- Use the email `testdo@example.com` to login as Dataset Owner.

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/login_dataset_owner.mp4" width="800px" controls></video>

### Register your dataset

To register your dataset, you need to collect the following information:

- A name you wish to have for your dataset.
- A small description of the dataset.
- The source location of your data (e.g., hospital name).
- The path to the data records (here, it is `medperf_tutorial/sample_raw_data/images`).
- The path to the labels of the data (here, it is `medperf_tutorial/sample_raw_data/labels`)
- The benchmark that you wish to participate in. This ensures your data in the next step will be prepared using the benchmark's data
preparation container.

> Note: You will be submitting general information about the data, not the data itself. The data never leaves your machine.

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/dataset_register.mp4" width="800px" controls></video>

### Prepare the dataset

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/dataset_prepare.mp4" width="800px" controls></video>

### Set dataset into operational mode

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/dataset_set_operational.mp4" width="800px" controls></video>

### Request participation

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/dataset_request_association.mp4" width="800px" controls></video>

## Accepting Inference Participation (Benchmark Owner)

Login as Benchmark Owner then accept inference participation requests (from the model owners and data owners)

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/bmk_approve_associations.mp4" width="800px" controls></video>

## Run Inference (Inference Data Owner)

Login as Dataset Owner and run the benchmark execution, and view the results

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/run_execution.mp4" width="800px" controls></video>

### View and Submit inference results

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/view_and_submit_results.mp4" width="800px" controls></video>

## Result collection (Benchmark Owner)

Login as Benchmark Owner and pull and view inference results from the medperf server

<video src="https://storage.googleapis.com/medperf-storage/webui_snippets/bmk_view_results.mp4" width="800px" controls></video>
