---
prepared_hash: 9d56e799a9e63a6c3ced056ebd67eb6381483381
tutorial_id: data
hide:
  - toc
---
![Overview](../tutorial_images/overview.png){class="tutorial-sticky-image-content"}
# Hands-on Tutorial for Data Owners

## Overview

This guide provides you with the necessary steps to use MedPerf as a Data Owner. The key tasks can be summarized as follows:

1. Prepare your data.
2. Submit your data information.
3. Request participation in a benchmark.
4. Execute the benchmark models on your dataset.
5. Submit a result.

It is assumed that you have the general testing environment [set up](setup.md).

{% include "getting_started/shared/before_we_start.md" %}

## 1. Prepare your Data

![Dataset Owner prepares the dataset](../tutorial_images/do-1-do-prepares-datset.png){class="tutorial-sticky-image-content"}
To prepare your data, you need to collect the following information:

- A name you wish to have for your dataset.
- A small description of the dataset.
- The source location of your data (e.g., hospital name).
- The path to the data records (here, it is `medperf_tutorial/sample_raw_data/images`).
- The path to the labels of the data (here, it is `medperf_tutorial/sample_raw_data/labels`)
- The benchmark ID that you wish to participate in. This ensures your data is prepared using the benchmark's data preparation MLCube.

!!! note
    The `data_path` and `labels_path` are determined according to the input path requirements of the data preparation MLCube. To ensure that your data is structured correctly, it is recommended to check with the Benchmark Committee for specific details or instructions.

In order to find the benchmark ID, you can execute the following command to view the list of available benchmarks.

```bash
medperf benchmark ls
```

The target benchmark ID here is `1`.

Run the following command to prepare your data (make sure you are in MedPerf's root folder):

```bash
medperf dataset create \
  --name "mytestdata" \
  --description "A tutorial dataset" \
  --location "My machine" \
  --data_path "medperf_tutorial/sample_raw_data/images" \
  --labels_path "medperf_tutorial/sample_raw_data/labels" \
  --benchmark 1
```

After that, your dataset will be successfully prepared! This command will also calculate some statistics on your dataset. These statistics, along with general information about the data, are going to be submitted to the MedPerf server in the next step.

## 2. Submit your Data Information

![Dataset Owner registers the dataset metadata](../tutorial_images/do-2-do-registers-dataset.png){class="tutorial-sticky-image-content"}
To submit your data information, you need to know the generated UID of your prepared dataset. Normally, you will see it in the output of the previous command. You can always check local datasets information by running:

```bash
medperf dataset ls --local
```

!!! note
    You will be submitting general information about the data, not the data itself. The data never leaves your machine.

The unique identifier for your generated data is `{{ page.meta.prepared_hash }}`.

Run the following command to submit your dataset information to the MedPerf server:

```bash
medperf dataset submit --data_uid {{ page.meta.prepared_hash }}
```

Once you run this command, the information to be submitted will be displayed on the screen and you will be asked to confirm your submission.

After successfully submitting your dataset, you can proceed to request participation in the benchmark by initiating an association request.

## 3. Request Participation

![Dataset Owner requests to participate in the benchmark](../tutorial_images/do-3-do-requests-participation.png){class="tutorial-sticky-image-content"}
For submitting the results of executing the benchmark models on your data in the future, you must associate your data with the benchmark.

Once you have submitted your dataset to the MedPerf server, it will be assigned a server UID, which you can find by running `medperf dataset ls --mine`. Your dataset's server UID is also `1`.

Run the following command to request associating your dataset with the benchmark:

```bash
medperf dataset associate --benchmark_uid 1 --data_uid 1
```

This command will first run the benchmark's reference model on your dataset to ensure your dataset is compatible with the benchmark workflow. Then, the association request information is printed on the screen, which includes an executive summary of the test mentioned. You will be prompted to confirm sending this information and initiating this association request.

#### How to proceed after requesting association

![Benchmark Committee accepts / rejects datasets](../tutorial_images/do-4-bc-accepts-rejects-datasets.png){class="tutorial-sticky-image-content"}
When participating with a real benchmark, you must wait for the Benchmark Committee to approve the association request. You can check the status of your association requests by running `medperf association ls`. The association is identified by the server UIDs of your dataset and the benchmark with which you are requesting association.

_For the sake of continuing the tutorial only_, run the following to simulate the benchmark committee approving your association (make sure you are in the MedPerf's root directory):

```bash
sh tutorials_scripts/simulate_data_association_approval.sh
```

You can verify if your association request has been approved by running `medperf association ls`.

## 4. Execute the Benchmark

![Dataset Owner runs Benchmark models](../tutorial_images/do-5-do-runs-models.png){class="tutorial-sticky-image-content"}
MedPerf provides a command that runs all the models of a benchmark effortlessly. You only need to provide two parameters:

- The benchmark ID you want to run, which is `1`.
- The server UID of your data, which is `1`.

For that, run the following command:

```bash
medperf benchmark run --benchmark 1 --data_uid 1
```

After running the command, you will receive a summary of the executions. You will see something similar to the following:

```text
  model  local result UID    partial result    from cache    error
-------  ------------------  ----------------  ------------  -------
      2  b1m2d1              False             True
      4  b1m4d1              False             False
Total number of models: 2
        1 were skipped (already executed), of which 0 have partial results
        0 failed
        1 ran successfully, of which 0 have partial results

✅ Done!
```

This means that the benchmark has two models:

- A model that you already ran when you requested the association. This explains why it was skipped.
- Another model that ran successfully. Its result generated UID is `b1m4d1`.

You can view the results by running the following command with the specific local result UID. For example:

```bash
medperf result view b1m4d1
```

For now, your results are only local. Next, you will learn how to submit the results.

## 5. Submit a Result

![Dataset Owner submits evaluation results](../tutorial_images/do-6-do-submits-eval-results.png){class="tutorial-sticky-image-content"}
After executing the benchmark, you will submit a result to the MedPerf server. To do so, you have to find the target result generated UID.

As an example, you will be submitting the result of UID `b1m4d1`. To do this, run the following command:

```bash
medperf result submit --result b1m4d1
```

The information that is going to be submitted will be printed to the screen and you will be prompted to confirm that you want to submit.

![The end](../tutorial_images/the-end.png){class="tutorial-sticky-image-content"}
{% include "getting_started/shared/cleanup.md" %}

## See Also

- [Running a Single Model.](../concepts/single_run.md)
