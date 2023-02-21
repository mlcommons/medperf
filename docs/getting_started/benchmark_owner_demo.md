## Overview

This guide will walk you through the essentials of how a benchmark owner can use MedPerf. The main tasks can be summarized as follows:

1. Define and implement a valid workflow
2. Develop a demo dataset
3. Submit the workflow components to the MedPerf server
4. Test your workflow
5. Submit the benchmark to the MedPerf server
6. Accept an association request

We assume that you had [set up the general testing environment](setup.md).

## Before We Start

#### Seed the server

For the purpose of the tutorial, you have to start with a fresh server database and seed it to create necessary entities that you will be interacting with. Run the following: (make sure you are in MedPerf's root folder)

```
cd server
sh reset_db.sh
python seed.py --cert cert.crt --demo benchmark
```

## 1. Providing a Valid Workflow

This is accomplished by submitting three [MLCubes](../mlcubes.md):

1. **The Data Preparator MLCube:** This MLCube will be used to transform raw data into a dataset ready for the AI model execution. All data owners willing to participate in this benchmark will have their data prepared using this MLCube. Details on how to implement data preparation MLCubes and hosting their files can be found [here](https://github.com/aristizabal95/mlcube_examples/tree/medperf-examples/medperf/data_preparator). (TODO: update once we have guides on creating mlcubes)

2. **The Reference Model MLCube:** This MLCube will contain an example model implementation for the desired AI task. It should be compatible with the data preparation MLCube (i.e. the outputs of the data preparation MLCube can be directly fed as inputs to this MLCube). Details on how to implement model MLCubes and hosting their files can be found [here](https://github.com/aristizabal95/mlcube_examples/tree/medperf-examples/medperf/model). (TODO: update once we have guides on creating mlcubes)

3. **The Metrics MLCube:** This MLCube will be responsible for evaluating the performance of a model. It should be compatible with the reference model MLCube (i.e. the outputs of the reference model MLCube can be directly fed as inputs to this MLCube). Details on how to implement metrics MLCubes and hosting their files can be found [here](https://github.com/aristizabal95/mlcube_examples/tree/medperf-examples/medperf/metrics). (TODO: update once we have guides on creating mlcubes)

For this tutorial, these MLCubes are already implemented and hosted, and can be found here: [Data Preparator](https://github.com/aristizabal95/medical/tree/65a7d3f9d40a03c665616c96819d655e619421c1/cubes/xrv_prep), [Reference Model](https://github.com/aristizabal95/medical/tree/65a7d3f9d40a03c665616c96819d655e619421c1/cubes/xrv_chex_densenet), [Metrics](https://github.com/aristizabal95/medical/tree/65a7d3f9d40a03c665616c96819d655e619421c1/cubes/metrics).

Next, we are going to submit these MLCubes to the MedPerf server.

## 2. Develop a Demo Dataset

A demo dataset is a reference dataset. It is needed to test the benchmark's workflow, and that happens in two scenarios:

1. It is used for testing the benchmark's default workflow. The MedPerf client runs a compatibility test of the benchmark's three mlcubes prior to its submission. The test is run using the demo dataset as input.

2. When a model owner wants to participate in the benchmark, the MedPerf client tests the compatibility of their model with the benchmark's data preparation cube and metrics cube. The test is run using the demo dataset as input.

The demo dataset should be provided following a specific format. See [this page](../concepts/demo_dataset.md) for detailed information.

The demo dataset should be hosted somewhere. See [this page](../concepts/hosting_files.md) for more information.

For this tutorial, we will be using a ready demo dataset. Feel free to [download](https://storage.googleapis.com/medperf-storage/xrv_demo_data.tar.gz) it and inspect its structure.

## 3. Test your Workflow

WIP

## 4. Submit the Workflow Components

The above components should be registered in the MedPerf server before using them as components of a benchmark. For detailed information about how mlcubes are submitted, refer to [this page](../concepts/mlcube_submit.md).

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

## 5. Submitting Your Benchmark

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

## 6. Approving Associations

WIP
