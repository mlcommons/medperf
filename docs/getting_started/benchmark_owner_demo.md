---
demo_url: https://storage.googleapis.com/medperf-storage/mock_xrv_demo_data.tar.gz
model_add: https://storage.googleapis.com/medperf-storage/xrv_chex_densenet.tar.gz
assets_url: https://raw.githubusercontent.com/hasan7n/medperf/88155cf4cac9b3201269d16e680d7d915a2f8adc/examples/ChestXRay/
tutorial_id: benchmark
---

# Hands-on Tutorial for Bechmark Committee

{% set prep_mlcube = assets_url+"chexpert_prep/mlcube/mlcube.yaml" %}
{% set prep_params = assets_url+"chexpert_prep/mlcube/workspace/parameters.yaml" %}
{% set model_mlcube = assets_url+"xrv_densenet/mlcube/mlcube.yaml" %}
{% set model_params = assets_url+"xrv_densenet/mlcube/workspace/parameters.yaml" %}
{% set metrics_mlcube = assets_url+"metrics/mlcube/mlcube.yaml" %}
{% set metrics_params = assets_url+"metrics/mlcube/workspace/parameters.yaml" %}

## Overview

This guide will walk you through the essentials of how a user can create a benchmark using MedPerf. The main tasks can be summarized as follows:

1. Implement a valid workflow
2. Develop a demo dataset
3. Test your workflow
4. Submitting the MLCubes to the MedPerf server
5. Host the demo dataset
6. Submit the benchmark to the MedPerf server

We assume that you had [set up the general testing environment](setup.md).

{% include "getting_started/shared/before_we_start.md" %}

## 1. Implement a Valid Workflow

This is accomplished by implementing three [MLCubes](../mlcubes/mlcubes.md):

1. **The Data Preparator MLCube:** This MLCube will be used to transform raw data into a dataset ready for the AI model execution. All data owners willing to participate in this benchmark will have their data prepared using this MLCube. A tutorial on how to implement data preparation MLCubes can be found [here](../mlcubes/mlcube_data.md).

2. **The Reference Model MLCube:** This MLCube will contain an example model implementation for the desired AI task. It should be compatible with the data preparation MLCube (i.e. the outputs of the data preparation MLCube can be directly fed as inputs to this MLCube). A tutorial on how to implement model MLCubes can be found [here](../mlcubes/mlcube_models.md).

3. **The Metrics MLCube:** This MLCube will be responsible for evaluating the performance of a model. It should be compatible with the reference model MLCube (i.e. the outputs of the reference model MLCube can be directly fed as inputs to this MLCube). A tutorial on how to implement metrics MLCubes can be found [here](../mlcubes/mlcube_metrics.md).

For this tutorial, we have already implemented the three mlcubes for the task of chest X-ray classification. The implementations can be found here: [Data Preparator](https://github.com/mlcommons/medperf/tree/main/examples/ChestXRay/chexpert_prep), [Reference Model](https://github.com/mlcommons/medperf/tree/main/examples/ChestXRay/xrv_densenet), [Metrics](https://github.com/mlcommons/medperf/tree/main/examples/ChestXRay/metrics). We have setup these mlcubes locally for you and can be found in your workspace folder under the names: `chexpert_prep`, `xrv_densenet`, and `metrics`.

## 2. Develop a Demo Dataset

A demo dataset is a small reference dataset. It contains a few data records and their labels, which will be used to test the benchmark's workflow in two scenarios:

1. It is used for testing the benchmark's default workflow. The MedPerf client automatically runs a compatibility test of the benchmark's three mlcubes prior to its submission. The test is run using the benchmark's demo dataset as input.

2. When a model owner wants to participate in the benchmark, the MedPerf client tests the compatibility of their model with the benchmark's data preparation cube and metrics cube. The test is run using the benchmark's demo dataset as input.

For this tutorial, we have already developed a demo dataset for the workflow provided in the previous section. The dataset can be found in your workspace folder under the name `mock_chexpert`. It is a mock dataset comprising of images and labels, which will serve as replacement of real X-ray images.

Now that we have our 3 MLCubes and the demo data, we can test the workflow. It is usually recommended to test the workflow before submitting any asset to the MedPerf server.

## 3. Test your Workflow

MedPerf provides a single command to test an inference workflow. To test your workflow with local MLCubes and local data, run: (make sure you are in MedPerf's root folder)

```bash
medperf test run \
   --data_preparation "medperf_tutorial/chexpert_prep/mlcube/mlcube.yaml" \ # (1)!
   --model "medperf_tutorial/xrv_densenet/mlcube/mlcube.yaml" \ # (2)!
   --evaluator "medperf_tutorial/metrics/mlcube/mlcube.yaml" \ # (3)!
   --data_path "medperf_tutorial/mock_chexpert/images" \ # (4)!
   --labels_path "medperf_tutorial/mock_chexpert/labels" \ # (5)!
```

1. Path to the data preparation MLCube manifest file.
2. Path to the model MLCube manifest file.
3. Path to the metrics MLCube manifest file.
4. Path to the demo dataset data records.
5. Path to the demo dataset data labels.

Assuming the test passes, we are ready to submit the MLCubes to the MedPerf server.

## 4. Submitting the MLCubes

#### How does MedPerf Recognize an MLCube?

{% include "getting_started/shared/mlcube_submission_overview.md" %}

To prepare the files of our three MLCubes, run (make sure you are in MedPerf's root folder):

```bash
python scripts/package-mlcube.py medperf_tutorial/chexpert_prep/mlcube
python scripts/package-mlcube.py medperf_tutorial/xrv_densenet/mlcube
python scripts/package-mlcube.py medperf_tutorial/metrics/mlcube
```

For each MLCube, this script will create a new folder in the MLCube directory, named `deploy`, containing all the files that should be hosted separately.

{% include "getting_started/shared/redirect_to_hosting_files.md" %}

#### Submit the MLCubes

To submit the MLCubes:

1. The Data Preparator MLCube:

    - The submission should include:

        a. The URL to the hosted mlcube manifest file:

        ```text
        {{ prep_mlcube }}

        ```

        b. The URL to the hosted mlcube parameters file:

        ```text
        {{ prep_params }}
        ```

    - The command to submit:

        ```bash
        medperf mlcube submit \
            --name my-prep-cube \
            --mlcube-file "{{ prep_mlcube }}" \
            --parameters-file "{{ prep_params }}" \
        ```

2. The Reference Model MLCube:

    - The submission should include:

        a. The URL to the hosted mlcube manifest file:

        ```text
        {{ model_mlcube }}
        ```

        b. The URL to the hosted mlcube parameters file:

        ```text
        {{ model_params }}
        ```

        c. The URL to the hosted additional files tarball file:

        ```text
        {{ model_add }}
        ```

    - Command to submit:

        ```bash
        medperf mlcube submit \
        --name my-modelref-cube \
        --mlcube-file "{{ model_mlcube }}" \
        --parameters-file "{{ model_params }}" \
        --additional-file "{{ model_add }}"
        ```

3. The Metrics MLCube:

    - The submission should include:

        a. The URL to the hosted mlcube manifest file:

        ```text
        {{ metrics_mlcube }}
        ```

        b. The URL to the hosted mlcube parameters file:

        ```text
        {{ metrics_params }}
        ```

    - Command to submit:

        ```bash
        medperf mlcube submit \
        --name my-metrics-cube \
        --mlcube-file "{{ metrics_mlcube }}" \
        --parameters-file "{{ metrics_params }}" \
        ```

Each of the three MLCubes will be assigned by a server UID. You can check them by running:

```bash
medperf mlcube ls --mine
```

Next, we will learn how to host the demo dataset.

## 5. Hosting the Demo Dataset

The demo dataset should be packaged in a specific way as a compressed tarball file. Looking at the folder stucture in the workspace:

```text
.
└── medperf_tutorial
    ├── mock_chexpert
    │   ├── images
    │   └── labels
    │
    ...
```

What we want to do is to package the folder `mock_chexpert`. We need first to create a file specifying how someone can find the data records path and the labels path. Create a file named `paths.yaml` that specifies the data records path and the labels path, as follows:

In your workspace directory (`medperf_tutorial`), create a file `paths.yaml` and fill it with the following:

```text
data_path: mock_chexpert/images
labels_path: mock_chexpert/labels
```

!!! note
    These paths are determined based on how the data preparation MLCube expects the input paths to be.

Now the workspace should look like this:

```text
.
└── medperf_tutorial
    ├── mock_chexpert
    │   ├── images
    │   └── labels
    ├── paths.yaml
    │
    ...
```

Finally, compress the required assets (`mock_chexpert` and `paths.yaml`) into a tarball file. In your workspace directory, run:

```bash
tar -czf mock_xrv_demo_data.tar.gz mock_chexpert paths.yaml
```

And that's it! Now you have to host the tarball file (`mock_xrv_demo_data.tar.gz`) on the internet.

For the tutorial to run smoothly, we already have the file hosted at this URL:

```text
{{ demo_url }}
```

If you wish to host it by yourself, you can find the list of supported options and details about hosting files in [this page](../concepts/hosting_files.md).

Finally, since we now have our MLCubes submitted and demo dataset hosted, we can submit the benchmark to the MedPerf server.

## 6. Submitting Your Benchmark

You need to keep at hand the following information:

- The Demo Dataset URL. In our case:

```text
{{ demo_url }}
```

- The server UIDs of the three MLCubes:
    - Data preparator UID: `1`
    - Reference model UID: `2`
    - Evaluator UID: `3`

You can create and submit your benchmark using the following command:

```bash
medperf benchmark submit \
   --name tutorial_bmk \
   --description "A benchmark created following MedPerf tutorial" \
   --demo-url "{{ demo_url }}" \
   --data-preparation-mlcube 1 \
   --reference-model-mlcube 2 \
   --evaluator-mlcube 3
```

The MedPerf client will first automatically run a compatibility test between the MLCubes using the demo dataset. If the test is successful, the benchmark will be submitted along with the compatibility test results.

!!! note
    The benchmark will stay inactive until the MedPerf admin approves your submission.

That's it! You check your benchmark's server UID by running:

```bash
medperf benchmark ls --mine
```

{% include "getting_started/shared/cleanup.md" %}

## See Also

- [Benchmark Associations.](../concepts/associations.md)
- [Models Priorities](../concepts/priorities.md)
