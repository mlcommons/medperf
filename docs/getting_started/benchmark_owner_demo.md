---
demo_url: https://storage.googleapis.com/medperf-storage/chestxray_tutorial/demo_data.tar.gz
model_add: https://storage.googleapis.com/medperf-storage/chestxray_tutorial/cnn_weights.tar.gz
assets_url: https://raw.githubusercontent.com/mlcommons/medperf/main/examples/chestxray_tutorial/
tutorial_id: benchmark
email: testbo@example.com
hide:
  - toc
---
![Overview](../tutorial_images/overview.png){class="tutorial-sticky-image-content"}

# Hands-on Tutorial for Bechmark Committee

{% set prep_container = assets_url+"data_preparator/container_config.yaml" %}
{% set prep_params = assets_url+"data_preparator/workspace/parameters.yaml" %}
{% set model_container = assets_url+"model_custom_cnn/container_config.yaml" %}
{% set model_params = assets_url+"model_custom_cnn/workspace/parameters.yaml" %}
{% set metrics_container = assets_url+"metrics/container_config.yaml" %}
{% set metrics_params = assets_url+"metrics/workspace/parameters.yaml" %}

## Overview

In this guide, you will learn how a user can use MedPerf to create a benchmark. The key tasks can be summarized as follows:

1. Implement a valid workflow.
2. Develop a demo dataset.
3. Test your workflow.
4. Submitting the Containers to the MedPerf server.
5. Host the demo dataset.
6. Submit the benchmark to the MedPerf server.

It's assumed that you have already set up the general testing environment as explained in the [installation](installation.md) and [setup guide](setup.md).

{% include "getting_started/shared/before_we_start.md" %}

## 1. Implement a Valid Workflow

![Benchmark Committee implements Containers for workflow](../tutorial_images/bc-1-bc-implements-mlcubes.png){class="tutorial-sticky-image-content"}
The implementation of a valid workflow is accomplished by implementing three [Containers](../containers/containers.md):

1. **Data Preparator Container:** This Container will transform raw data into a dataset ready for the AI model execution. All data owners willing to participate in this benchmark will have their data prepared using this Container. A guide on how to implement MedPerf-compatible data preparation Containers can be found [here](../containers/containers.md).

2. **Reference Model Container:** This Container will contain an example model implementation for the desired AI task. It should be compatible with the data preparation Container (i.e., the outputs of the data preparation Container can be directly fed as inputs to this Container). A guide on how to implement MedPerf-compatible model Containers can be found [here](../containers/containers.md).

3. **Metrics Container:** This Container will be responsible for evaluating the performance of a model. It should be compatible with the reference model Container (i.e., the outputs of the reference model Container can be directly fed as inputs to this Container). A guide on how to implement MedPerf-compatible metrics Containers can be found [here](../containers/containers.md).

For this tutorial, you are provided with following three already implemented containers for the task of chest X-ray classification. The implementations can be found in the following links: [Data Preparator](https://github.com/mlcommons/medperf/tree/main/examples/chestxray_tutorial/data_preparator), [Reference Model](https://github.com/mlcommons/medperf/tree/main/examples/chestxray_tutorial/model_custom_cnn), [Metrics](https://github.com/mlcommons/medperf/tree/main/examples/chestxray_tutorial/metrics). These containers are setup locally for you and can be found in your workspace folder under `data_preparator`, `model_custom_cnn`, and `metrics`.

## 2. Develop a Demo Dataset

![Benchmark Committee develops a demo dataset](../tutorial_images/bc-2-bc-develops-dataset.png){class="tutorial-sticky-image-content"}
A demo dataset is a small reference dataset. It contains a few data records and their labels, which will be used to test the benchmark's workflow in two scenarios:

1. It is used for testing the benchmark's default workflow. The MedPerf client automatically runs a compatibility test of the benchmark's three containers prior to its submission. The test is run using the benchmark's demo dataset as input.

2. When a model owner wants to participate in the benchmark, the MedPerf client tests the compatibility of their model with the benchmark's data preparation container and metrics container. The test is run using the benchmark's demo dataset as input.

For this tutorial, you are provided with a demo dataset for the chest X-ray classification workflow. The dataset can be found in your workspace folder under `demo_data`. It is a small dataset comprising two chest X-ray images and corresponding thoracic disease labels.

You can test the workflow now that you have the three containers and the demo data. Testing the workflow before submitting any asset to the MedPerf server is usually recommended.

## 3. Test your Workflow

MedPerf provides a single command to test an inference workflow. To test your workflow with local containers and local data, the following need to be passed to the command:

1. Path to the data preparation container config file: `medperf_tutorial/data_preparator/container_config.yaml`.
2. Path to the model container config file: `medperf_tutorial/model_custom_cnn/container_config.yaml`.
3. Path to the metrics container config file: `medperf_tutorial/metrics/container_config.yaml`.
4. Path to the demo dataset data records: `medperf_tutorial/demo_data/images`.
5. Path to the demo dataset data labels. `medperf_tutorial/demo_data/labels`.

Run the following command to execute the test ensuring you are in MedPerf's root folder:

```bash
medperf test run \
   --data_preparator "medperf_tutorial/data_preparator/container_config.yaml" \
   --model "medperf_tutorial/model_custom_cnn/container_config.yaml" \
   --evaluator "medperf_tutorial/metrics/container_config.yaml" \
   --data_path "medperf_tutorial/demo_data/images" \
   --labels_path "medperf_tutorial/demo_data/labels"
```

Assuming the test passes successfully, you are ready to host the benchmark assets.

## 4. Host the Demo Dataset

The demo dataset should be packaged in a specific way as a compressed tarball file. The folder stucture in the workspace currently looks like the following:

```text
.
└── medperf_tutorial
    ├── demo_data
    │   ├── images
    │   └── labels
    │
    ...
```

The goal is to package the folder `demo_data`. You must first create a file called `paths.yaml`. This file will provide instructions on how to locate the data records path and the labels path. The `paths.yaml` file should specify both the data records path and the labels path.

In your workspace directory (`medperf_tutorial`), create a file `paths.yaml` and fill it with the following:

```text
data_path: demo_data/images
labels_path: demo_data/labels
```

!!! note
    The paths are determined by the Data Preparator container's expected input path.

After that, the workspace should look like the following:

```text
.
└── medperf_tutorial
    ├── demo_data
    │   ├── images
    │   └── labels
    ├── paths.yaml
    │
    ...
```

Finally, compress the required assets (`demo_data` and `paths.yaml`) into a tarball file by running the following command:

```bash
cd medperf_tutorial
tar -czf demo_data.tar.gz demo_data paths.yaml
cd ..
```

And that's it! Now you have to host the tarball file (`demo_data.tar.gz`) on the internet.

For the tutorial to run smoothly, the file is already hosted at the following URL:

```text
{{ demo_url }}
```

If you wish to host it by yourself, you can find the list of supported options and details about hosting files in [this page](../concepts/hosting_files.md).

## 5. Submitting the Containers

![Benchmark Committee submits Containers](../tutorial_images/bc-3-bc-submits-mlcubes.png){class="tutorial-sticky-image-content"}

### How does MedPerf Recognize a Container?

{% include "getting_started/shared/container_submission_overview.md" %}

{% include "getting_started/shared/redirect_to_hosting_files.md" %}

### Submit the Containers

#### Data Preparator Container

![Benchmark Committee submits the Data Preparator Container](../tutorial_images/bc-4-bc-submits-data-preparator.png){class="tutorial-sticky-image-content"}
In this tutorial, for the Data Preparator container, the submission should include:

- The URL to the hosted container configuration file, which is:

    ```text
    {{ prep_container }}

    ```

- The URL to the hosted parameters file, which is:

    ```text
    {{ prep_params }}
    ```

Use the following command to submit:

```bash
medperf container submit \
    --name my-prep \
    --container-config-file "{{ prep_container }}" \
    --parameters-file "{{ prep_params }}" \
    --operational
```

#### Reference Model Container

![Benchmark Committee submits the reference Model Container](../tutorial_images/bc-5-bc-submits-ref-model.png){class="tutorial-sticky-image-content"}
In this tutorial, for the Reference Model container, the submission should include:

- The URL to the hosted container configuration file:

    ```text
    {{ model_container }}
    ```

- The URL to the hosted parameters file:

    ```text
    {{ model_params }}
    ```

- The URL to the hosted additional files tarball file:

    ```text
    {{ model_add }}
    ```

Use the following command to submit:

```bash
medperf container submit \
--name my-refmodel \
--container-config-file "{{ model_container }}" \
--parameters-file "{{ model_params }}" \
--additional-file "{{ model_add }}" \
--operational
```

#### Metrics Container

![Benchmark Committee submits the Evaluation Metrics Container](../tutorial_images/bc-6-bc-submits-evalmetrics.png){class="tutorial-sticky-image-content"}
In this tutorial, for the Metrics container, the submission should include:

- The URL to the hosted container configuration file:

    ```text
    {{ metrics_container }}
    ```

- The URL to the hosted parameters file:

    ```text
    {{ metrics_params }}
    ```

Use the following command to submit:

```bash
medperf container submit \
--name my-metrics \
--container-config-file "{{ metrics_container }}" \
--parameters-file "{{ metrics_params }}" \
--operational
```

Each of the three containers will be assigned by a server UID. You can check the server UID for each container by running:

```bash
medperf container ls --mine
```

Finally, now after having the containers submitted and the demo dataset hosted, you can submit the benchmark to the MedPerf server.

## 6. Submit your Benchmark

![Benchmark Committee submits the Benchmark Metadata](../tutorial_images/bc-7-bc-submits-benchmark.png){class="tutorial-sticky-image-content"}
You need to keep at hand the following information:

- The Demo Dataset URL. Here, the URL will be:

```text
{{ demo_url }}
```

- The server UIDs of the three containers can be found by running:

```bash
 medperf container ls
```

- For this tutorial, the UIDs are as follows:
  - Data preparator UID: `1`
  - Reference model UID: `2`
  - Evaluator UID: `3`

You can create and submit your benchmark using the following command:

```bash
medperf benchmark submit \
   --name tutorial_bmk \
   --description "MedPerf demo bmk" \
   --demo-url "{{ demo_url }}" \
   --data-preparation-container 1 \
   --reference-model-container 2 \
   --evaluator-container 3 \
   --operational
```

The MedPerf client will first automatically run a compatibility test between the containers using the demo dataset. If the test is successful, the benchmark will be submitted along with the compatibility test results.

That's it! You can check your benchmark's server UID by running:

```bash
medperf benchmark ls --mine
```

![The end of the tutorial](../tutorial_images/the-end.png){class="tutorial-sticky-image-content"}
{% include "getting_started/shared/cleanup.md" %}

<!--
TODO: uncomment once pages are filled
## See Also

- [Benchmark Associations.](../concepts/associations.md)
- [Models Priorities](../concepts/priorities.md)
-->
