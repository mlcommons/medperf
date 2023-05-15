---
demo_url: https://storage.googleapis.com/medperf-storage/mock_xrv_demo_data.tar.gz
model_add: https://storage.googleapis.com/medperf-storage/xrv_pc_densenet.tar.gz
assets_url: https://raw.githubusercontent.com/hasan7n/medperf/88155cf4cac9b3201269d16e680d7d915a2f8adc/examples/ChestXRay/
tutorial_id: model
---

# Hands-on Tutorial for Model Owners

{% set model_mlcube = assets_url+"xrv_densenet/mlcube/mlcube.yaml" %}
{% set model_params = assets_url+"xrv_densenet/mlcube/workspace/parameters_pc.yaml" %}

## Overview

This guide will walk you through the essentials of how a model owner can use MedPerf to participate in a benchmark. We highly recommend to the user to follow [this](../mlcubes/mlcube_models.md) or [this](../mlcubes/gandlf_mlcube.md) tutorial first to implement their own model MLCube and use it throughout this tutorial. However, we provide an already implemented MLCube in case they want to directly proceed to learn how to interact with MedPerf.

The main tasks of this tutorial can be summarized as follows:

1. Test your MLCube compatibility with the benchmark
2. Submit your MLCube
3. Request participation in a benchmark

We assume that you had [set up the general testing environment](setup.md).

{% include "getting_started/shared/before_we_start.md" %}

## 1. Test your MLCube Compatibility

Before submitting your MLCube, it's highly recommended that you test your MLCube compatibility with the benchmarks of interest to avoid later edits and multiple submissions. Your MLCube should be compatible with the benchmark workflow in two main ways:

1. It should expect a certain data input structure
2. Its outputs should follow a certain structure expected by the benchmark's metrics evaluator MLCube

These details usually should be acquired by reaching out to the benchmark committee and following their instructions.

To test your MLCube validity with the benchmark, first run `medperf benchmark ls` to identify the benchmark's server UID. In our case, it is going to be `1`.

Next, locate the MLCube. Unless you implemented your own MLCube, the MLCube we will be using is `medperf_tutorial/xrv_densenet/mlcube/mlcube.yaml`.

Now run the compatibility test:

```bash
medperf test run \
   --benchmark 1 \
   --model "medperf_tutorial/xrv_densenet/mlcube/mlcube.yaml"

```

Assuming the test passes, we are ready to submit the MLCube to the MedPerf server.

## 2. Submitting the MLCube

#### How does MedPerf Recognize an MLCube?

{% include "getting_started/shared/mlcube_submission_overview.md" %}

To prepare the files of our three MLCubes, run (make sure you are in MedPerf's root folder):

```bash
python scripts/package-mlcube.py medperf_tutorial/xrv_densenet/mlcube
```

This script will create a new folder in the MLCube directory, named `deploy`, containing all the files that should be hosted separately.

{% include "getting_started/shared/redirect_to_hosting_files.md" %}

#### Submit the MLCube

The submission should include the URLs of all the hosted files. For our tutorial's MLCube:

a. The URL to the hosted mlcube manifest file:

```text
{{ page.meta.model_mlcube }}
```

b. The URL to the hosted mlcube parameters file:

```text
{{ page.meta.model_params }}
```

c. The URL to the hosted additional files tarball file:

```text
{{ page.meta.model_add }}
```

Command to submit:

```bash
medperf mlcube submit \
   --name my-modelref-cube \
   --mlcube-file "{{ page.meta.model_mlcube }}" \
   --parameters-file "{{ page.meta.model_params }}" \
   --additional-file "{{ page.meta.model_add }}"
```

The MLCube will be assigned by a server UID. You can check it by running:

```bash
medperf mlcube ls --mine
```

## 3. Request Participation

Benchmarks are run by data owners. Data owners will get notified when a new model was added to a benchmark so that they can run the model and submit a new result to the benchmark. In order for your model to be part of the benchmark, you have to request association.

To initiate an association request, you need to collect these information:

- The target benchmark ID, which is `1`
- The server UID of your MLCube, which is `4`.

Run the following command to request associating your MLCube with the benchmark:

```bash
medperf mlcube associate --benchmark 1 --model_uid 4
```

This command will first run the benchmark's workflow on your model to ensure it is compatible. After that, the association request information are printed to the screen, which includes an execution summary of the test mentioned. You will be prompted to confirm sending these information and initiating this association request.

#### What Happens After Requesting the Association?

When you are participating with a real benchmark, you have to wait for the benchmark committee to approve the association request. You can check the status of your association requests by running `medperf association ls`. The association is identified by the server UIDs of your MLCube and the benchmark you are requesting to be associated with.

{% include "getting_started/shared/cleanup.md" %}
