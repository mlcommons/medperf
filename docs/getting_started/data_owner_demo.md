---
prepared_hash: fe5f74f8e345662b81acb53d8558a39fbec75837
tutorial_id: data
---
# Hands-on Tutorial for Data Owners

## Overview

This guide will walk you through the essentials of how a data owner can use MedPerf. The main tasks can be summarized as follows:

1. Prepare your data
2. Submit your data information
3. Request participation in a benchmark
4. Execute the benchmark models on your dataset
5. Submit a result

We assume that you had [set up the general testing environment](setup.md).

{% include "getting_started/shared/before_we_start.md" %}

## 1. Prepare Your Data

To prepare your data, you need to collect these information:

- A name you wish to have for your dataset
- A small description of the dataset
- The source location of your data (e.g. hospital name)
- The path to the data records: in our case it is `medperf_tutorial/mock_chexpert/images`
- The path to the labels of the data: in our case it is `medperf_tutorial/mock_chexpert/labels`
- The benchmark ID that you wish to participate in. This is to ensure that your data is prepared using the benchmark's data preparation MLCube.

!!! note
    `data_path` and `labes_path` are determined based on how the data preparation MLCube expects the input paths to be. You usually know this by checking or asking for details from the benchmark committee on how they expect your data to be structured.

To get the benchmark ID, you can run the following command to see what benchmarks are available:

```bash
medperf benchmark ls
```

You will find that our target benchmark ID is `1`.

Run the following command to prepare your data (make sure you are in MedPerf's root folder):

```bash
medperf dataset create \
  --name "mytestdata" \
  --description "A tutorial dataset" \
  --location "My machine" \
  --data_path "medperf_tutorial/mock_chexpert/images" \
  --labels_path "medperf_tutorial/mock_chexpert/labels" \
  --benchmark 1
```

Your dataset is successfully prepared! This command will also calculate some statistics on your dataset. These statistics, along with general information about the data, are going to be submitted to the MedPerf server in the next step.

## 2. Submit your data information

Note that you will be submitting general information about the data, not the data itself. The data never leaves your machine.

To submit your data information, you need to know the generated UID of your prepared dataset. Normally, you will see it in the output of the previous command. You can always check local datasets information by running:

```bash
medperf dataset ls --local
```

You will find that the generated uid is `{{ page.meta.prepared_hash }}`.

Run the following command to submit your dataset information to the MedPerf server:

```bash
medperf dataset submit --data_uid {{ page.meta.prepared_hash }}
```

The information that is going to be submitted will be printed to the screen and you will be prompted to confirm that you want to submit.

Your dataset is successfully submitted! Next, request participation in the benchmark by initiating an association request.

## 3. Request Participation

In order to be able later on to submit results of executing the benchmark models on your data, your data has to be associated with the benchmark.

To initiate an association request, you need to collect these information:

- The target benchmark ID, which is `1`
- The server UID of your data.

After you submitted your dataset to the server, it is assigned with a server UID. You can run `medperf dataset ls --mine` to find your dataset's server UID.

You will find that your dataset server UID is `1`.

Run the following command to request associating your dataset with the benchmark:

```bash
medperf dataset associate --benchmark_uid 1 --data_uid 1
```

This command will first run the benchmark's reference model on your dataset to ensure your dataset is compatible with the benchmark workflow. After that, the association request information are printed to the screen, which includes an execution summary of the test mentioned. You will be prompted to confirm sending these information and initiating this association request.

#### What Happens After Requesting the Association?

When you are participating with a real benchmark, you have to wait for the benchmark committee to approve the association request. You can check the status of your association requests by running `medperf association ls`. The association is identified by the server UIDs of your dataset and the benchmark you are requesting to be associated with.

_For the sake of continuing our tutorial only_, run the following to simulate the benchmark committee approving your association (make sure you are in the MedPerf's root directory):

```bash
sh tutorials_scripts/simulate_data_association_approval.sh
```

You can check now that your association request has been approved by running `medperf association ls`.

## 4. Execute the Benchmark

It is time to run the benchmark! We provide a command that runs all models associated with a benchmark. To do that all you need is:

- The target benchmark ID, which is `1`
- The server UID of your data, which is `1`

Run the following command:

```bash
medperf benchmark run --benchmark 1 --data_uid 1
```

You will see at the end a summary of the executions. In our case, you will see something similar to the following:

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

- A model that you already have run when you requested the association. This explains why it was skipped.
- Another model which ran successfully. Its result generated UID is `b1m4d1`.

You can view the results by their UID. For example:

```bash
medperf result view b1m4d1
```

For now, your results are only local. Next, you will learn how to submit the results.

## 5. Submit a Result

We are going now to submit a result to the MedPerf server. To do so, you have to find the target result generated UID.

We will be submitting the result of UID `b1m4d1`. Run the following command:

```bash
medperf result submit --result b1m4d1
```

The information that is going to be submitted will be printed to the screen and you will be prompted to confirm that you want to submit.

{% include "getting_started/shared/cleanup.md" %}

## See Also

- [Running a Single Model.](../concepts/single_run.md)
