## Overview

This guide will walk you through the essentials of how a benchmark owner can use MedPerf. The main tasks can be summarized as follows:

1. Implement a valid workflow
2. Develop a demo dataset
3. Test your workflow
4. Host the components' files on the internet
5. Submit the workflow components to the MedPerf server
6. Submit the benchmark to the MedPerf server
7. Accept an association request

We assume that you had [set up the general testing environment](setup.md).

## Before We Start

#### Seed the server

For the purpose of the tutorial, you have to start with a fresh server database and seed it to create necessary entities that you will be interacting with. Run the following: (make sure you are in MedPerf's root folder)

```
cd server
sh reset_db.sh
python seed.py --cert cert.crt --demo benchmark
```

#### Download the Necessary files

We provide a script that downloads necessary files so that you follow the tutorial smoothly. Run the following: (make sure you are in MedPerf's root folder)

```
sh tutorials_scripts/setup_benchmark_tutorial.sh
```

This will create a workspace folder `medperf_tutorial` where all necessary files are downloaded.

## 1. Implement a Valid Workflow

This is accomplished by implementing three [MLCubes](../mlcubes/mlcubes.md):

1. **The Data Preparator MLCube:** This MLCube will be used to transform raw data into a dataset ready for the AI model execution. All data owners willing to participate in this benchmark will have their data prepared using this MLCube. A tutorial on how to implement data preparation MLCubes can be found [here](../mlcubes/mlcube_data.md).

2. **The Reference Model MLCube:** This MLCube will contain an example model implementation for the desired AI task. It should be compatible with the data preparation MLCube (i.e. the outputs of the data preparation MLCube can be directly fed as inputs to this MLCube). A tutorial on how to implement model MLCubes can be found [here](../mlcubes/mlcube_models.md).

3. **The Metrics MLCube:** This MLCube will be responsible for evaluating the performance of a model. It should be compatible with the reference model MLCube (i.e. the outputs of the reference model MLCube can be directly fed as inputs to this MLCube). A tutorial on how to implement metrics MLCubes can be found [here](../mlcubes/mlcube_metrics.md).

For this tutorial, we have already implemented the three mlcubes for the task of chest X-ray classification. The implementations can be found here: [Data Preparator](https://github.com/mlcommons/medperf/tree/main/examples/ChestXRay/chexpert_prep), [Reference Model](https://github.com/mlcommons/medperf/tree/main/examples/ChestXRay/xrv_chex_densenet), [Metrics](https://github.com/mlcommons/medperf/tree/main/examples/ChestXRay/metrics). We have setup these mlcubes locally for you and can be found in your workspace folder under the names: `chexpert_prep`, `xrv_chex_densenet`, and `metrics`.

## 2. Develop a Demo Dataset

A demo dataset is a small reference dataset. It contains a few data records and their labels, which will be used to test the benchmark's workflow in two scenarios:

1. It is used for testing the benchmark's default workflow. The MedPerf client automatically runs a compatibility test of the benchmark's three mlcubes prior to its submission. The test is run using the benchmark's demo dataset as input.

2. When a model owner wants to participate in the benchmark, the MedPerf client tests the compatibility of their model with the benchmark's data preparation cube and metrics cube. The test is run using the benchmark's demo dataset as input.

For this tutorial, we have already developed a demo dataset for the workflow provided in the previous section. The dataset can be found in your workspace folder under the name `mock_chexpert`.

Now that we have our 3 MLCubes and the demo data, we can test the workflow. It is usually recommended to test the validity of the workflow before submitting any asset to the MedPerf server.

## 3. Test your Workflow

MedPerf provides a single command to test an inference workflow. To test your workflow with local MLCubes and local data, run: (make sure you are in MedPerf's root folder)

```bash
medperf test run \
   --data_preparation "medperf_tutorial/chexpert_prep" \ # (1)!
   --model "medperf_tutorial/xrv_chex_densenet" \ # (2)!
   --evaluator "medperf_tutorial/metrics" \ # (3)!
   --data_path "medperf_tutorial/mock_chexpert/images" \ # (4)!
   --labels_path "medperf_tutorial/mock_chexpert/labels" \ # (5)!
```

1. Path to the data preparation MLCube folder.
2. Path to the model MLCube folder.
3. Path to the metrics MLCube folder.
4. Path to the demo dataset data records.
5. Path to the demo dataset data labels.

Assuming the test passes, we are ready to host the necessary files of the MLCubes and the demo dataset.

## 4. Submitting the MLCubes Files

We refer the reader to [this page](../concepts/hosting_mlcube_files.md) to know how mlcubes can be submitted.

## 5. Hosting the Demo Dataset

The demo dataset should be packaged in a specific way as a compressed tarball file. Looking at the folder stucture in the workspace:

```
.
└── medperf_tutorial
    ├── mock_chexpert
    │   ├── images
    │   └── labels
    │
    ...
```

What we want to do is to package the folder `mock_chexpert`. We need first to create a file specifying how someone can find the data records path and the labels path. Create a file named `paths.yaml` that specifies the data records path and the labels path, as follows:

In your workspace directory, create a file `paths.yaml` and fill it with the following:

```
data_path: mock_chexpert/images
labels_path: mock_chexpert/labels
```

# say that they can be the same path

!!! note
These paths are determined based on how the data preparation MLCube expects the input paths to be. For example,

Now the workspace should look like this:

```
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

```
tar -czf demo_data.tar.gz mock_chexpert paths.yaml
```

And that's it! Now you have to host the tarball file (`demo_data.tar.gz`) on the internet. For supported options and details about hosting files, refer to [this page](../concepts/hosting_files.md).

Next, since we now have our MLCube files hosted, we will register the MLCubes to the MedPerf server.

## 5. Submit the Workflow MLCubes

The 3 MLCubes should be registered in the MedPerf server before using them as components of a benchmark. For detailed information about how mlcubes are submitted, refer to [this page](../concepts/mlcube_submit.md).

To submit these MLCubes:

1. The Data Preparator MLCube: the submission should include:

   a. The URL to the mlcube manifest: `<link>`

   b. The URL to the mlcube parameters file: `<link>`

   c. The URL to the Singularity image of the MLCube. This is needed if the MLCube is going to be run with Singularity.

```
medperf mlcube submit \
   --name my-prep-cube \
   --mlcube-file <link> \
   --parameters-file <link> \
   --image-file <link>
```

2. The Reference Model MLCube: the submission should include:

   a. The URL to the mlcube manifest: `<link>`

   b. The URL to the mlcube parameters file: `<link>`

   c. The URL to the Singularity image of the MLCube. This is needed if the MLCube is going to be run with Singularity.

   d. The URL to the additional files of the MLCube. These will include the weights of the model.

```
medperf mlcube submit \
   --name my-modelref-cube \
   --mlcube-file <link> \
   --parameters-file <link> \
   --image-file <link> \
   --additional-file <link>
```

3. The Metrics MLCube: the submission should include:

   a. The URL to the mlcube manifest: `<link>`

   b. The URL to the mlcube parameters file: `<link>`

   c. The URL to the Singularity image of the MLCube. This is needed if the MLCube is going to be run with Singularity.

```
medperf mlcube submit \
   --name my-metrics-cube \
   --mlcube-file <link> \
   --parameters-file <link> \
   --image-file <link>

```

Each of the three MLCubes will be assigned by a server UID that be checked by running:

```
medperf mlcube ls
```

## 6. Submitting Your Benchmark

Once all your cubes are submitted to the platform, you can create and submit your benchmark. For this, you need to keep at hand the following information:

- Demo Dataset URL. In our case: [https://storage.googleapis.com/medperf-storage/xrv_demo_data.tar.gz](https://storage.googleapis.com/medperf-storage/xrv_demo_data.tar.gz)
- The server UIDs of the three MLCubes submitted in the previous section:
  - Data preparator UID: 1
  - Reference model UID: 2
  - Evaluator UID: 3

You can create and submit your benchmark using the following command:

```
medperf benchmark submit \
   --name <benchmark_name> \
   --description <benchmark_description> \
   --demo-url <demo_url> \
   --data-preparation-mlcube <data_preparator_MLCube_uid> \
   --reference-model-mlcube <model_MLCube_uid> \
   --evaluator-mlcube <evaluator_MLCube_uid>
```

The MedPerf client will first run a compatibility test between the MLCubes using the demo dataset. If the test is successful, the benchmark will be submitted along with the test results.

The benchmark will stay inactive until the MedPerf admin approves your submission.

## 7. Approving Associations

WIP
