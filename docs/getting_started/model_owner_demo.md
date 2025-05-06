---
demo_url: https://storage.googleapis.com/medperf-storage/chestxray_tutorial/demo_data.tar.gz
model_add: https://storage.googleapis.com/medperf-storage/chestxray_tutorial/mobilenetv2_weights.tar.gz
assets_url: https://raw.githubusercontent.com/mlcommons/medperf/main/examples/chestxray_tutorial/
tutorial_id: model
hide:
  - toc
---
![Overview](../tutorial_images/overview.png){class="tutorial-sticky-image-content"}

# Hands-on Tutorial for Model Owners

{% set model_container = assets_url+"model_mobilenetv2/container_config.yaml" %}
{% set model_params = assets_url+"model_mobilenetv2/workspace/parameters.yaml" %}

## Overview

In this guide, you will learn how a Model Owner can use MedPerf to take part in a benchmark. Usuall as a model owner you may be also interested in how to build a [MedPerf-compatible model container](../containers/containers.md#model-container). But this guide provides an already implemented container if you want to directly proceed to learn how to interact with MedPerf.

The main tasks of this guide are:

1. Testing container compatibility with the benchmark.
2. Submitting the container.
3. Requesting participation in a benchmark.

It's assumed that you have already set up the general testing environment as explained in the [setup guide](setup.md).

{% include "getting_started/shared/before_we_start.md" %}

## 1. Test your Container Compatibility

![Model Owner implements & tests Container](../tutorial_images/mo-1-mo-implements-cube.png){class="tutorial-sticky-image-content"}
Before submitting your container, it is highly recommended that you test your container compatibility with the benchmarks of interest to avoid later edits and multiple submissions. Your container should be compatible with the benchmark workflow in two main ways:

1. It should expect a specific data input structure
2. Its outputs should follow a particular structure expected by the benchmark's metrics evaluator container

These details should usually be acquired by contacting the Benchmark Committee and following their instructions.

To test your container validity with the benchmark, first run `medperf benchmark ls` to identify the benchmark's server UID. In this tutorial, it is going to be `1`.

Next, locate the container. Unless you implemented your own container, the container provided for this tutorial is located in your workspace: `medperf_tutorial/model_mobilenetv2/container_config.yaml`.

After that, run the compatibility test:

```bash
medperf test run \
   --benchmark 1 \
   --model "medperf_tutorial/model_mobilenetv2/container_config.yaml"

```

Assuming the test passes successfuly, you are ready to submit the container to the MedPerf server.

## 2. Submit the Container

![Model Owner submits Model Container](../tutorial_images/mo-2-mo-submits-model.png){class="tutorial-sticky-image-content"}

### How does MedPerf Recognize an Container?

{% include "getting_started/shared/mlcube_submission_overview.md" %}

{% include "getting_started/shared/redirect_to_hosting_files.md" %}

### Submit the Container

The submission should include the URLs of all the hosted assets. For the Container provided for the tutorial:

- The URL to the hosted container configuration file is

   ```text
   {{ model_container }}
   ```

- The URL to the hosted parameters file is

   ```text
   {{ model_params }}
   ```

- The URL to the hosted additional files tarball file is

   ```text
   {{ page.meta.model_add }}
   ```

Use the following command to submit:

```bash
medperf container submit \
   --name my-model \
   --container-config-file "{{ model_container }}" \
   --parameters-file "{{ model_params }}" \
   --additional-file "{{ page.meta.model_add }}" \
   --operational
```

The container will be assigned by a server UID. You can check it by running:

```bash
medperf container ls --mine
```

## 3. Request Participation

![Model Owner requests to participate in the benchmark](../tutorial_images/mo-3-mo-requests-participation.png){class="tutorial-sticky-image-content"}
Benchmark workflows are run by Data Owners, who will get notified when a new model is added to a benchmark. You must request the association for your model to be part of the benchmark.

To initiate an association request, you need to collect the following information:

- The target benchmark ID, which is `1`
- The server UID of your container, which is `4`.

Run the following command to request associating your container with the benchmark:

```bash
medperf container associate --benchmark 1 --model_uid 4
```

This command will first run the benchmark's workflow on your model to ensure your model is compatible with the benchmark workflow. Then, the association request information is printed on the screen, which includes an executive summary of the test mentioned. You will be prompted to confirm sending this information and initiating this association request.

#### What Happens After Requesting the Association?

![Benchmark Committee accepts / rejects models](../tutorial_images/mo-4-bc-accepts-rejects-models.png){class="tutorial-sticky-image-content"}
When participating with a real benchmark, you must wait for the Benchmark Committee to approve the association request. You can check the status of your association requests by running `medperf association ls -bm`. The association is identified by the server UIDs of your container and the benchmark with which you are requesting association.

![The end](../tutorial_images/the-end.png){class="tutorial-sticky-image-content"}
{% include "getting_started/shared/cleanup.md" %}
