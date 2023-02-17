## Overview

This guide will walk you through the essentials of how a data owner can use MedPerf. The main tasks can be summarized as follows:

1. [Prepare your data](#1-prepare-your-data)
2. [Submit your data information](#2-submit-your-data-information)
3. [Request participation in a benchmark](#3-request-participation)
4. [Execute the benchmark models on your dataset](#4-execute-the-benchmark-models-on-your-dataset)
5. [Submit a result](#5-submit-a-result)

We assume that you had [set up the general testing environment](setup.md).

## Before We Start

#### Seed the server

For the purpose of the tutorial, you have to start with a fresh server database and seed it to create benchmarks and MLCubes that you will be interacting with. Run the following: (make sure you are in MedPerf's root folder)

```
cd server
sh reset_db.sh
python seed.py --cert cert.crt --demo data
```

#### Download the Dataset

You need data to test this tutorial. We provide a mock dataset comprising of images and labels, which will serve as replacement of real X-ray images. You can download it by running:

```
wget -P /tmp/medperf_test_files https://storage.googleapis.com/medperf-storage/mock_chexpert_dset.tar.gz
tar -xzvf /tmp/medperf_test_files/mock_chexpert_dset.tar.gz -C /tmp/medperf_test_files
```

This will download and extract the data under the folder `/tmp/medperf_test_files`.

#### Login to the Local Server

You credentials in this tutorial will be a username: `testdataowner` and a password: `test`. Run:

```
medperf login
```

You will be prompted to enter your credentials.

You are now ready to start!

## 1. Prepare Your Data

To prepare your data, you need to collect these information:

- A name you wish to have for your dataset
- A small description of the dataset
- The source location of your data (e.g. hospital name)
- The path to the data: in our case it is `/tmp/medperf_test_files/mock_chexpert`
- The path to the labels of the data: in our case it is the same as above `/tmp/medperf_test_files/mock_chexpert`
- The benchmark ID that you wish to participate in. This is to ensure that your data is prepared using the benchmark's data preparation MLCube.

For the last piece of information, you can run the following command to see what benchmarks are available:

```
medperf benchmark ls
```

You will find that our target benchmark ID is `1`.

Run the following command to prepare your data:

```
medperf dataset create \
  --name "mytestdata" \
  --description "A mock dataset to run MedPerf demo"
  --location "here"
  --data_path "/tmp/medperf_test_files/mock_chexpert" \
  --labels_path "/tmp/medperf_test_files/mock_chexpert" \
  --benchmark 1
```

Your dataset is successfully prepared! This command will also calculate some statistics on your dataset. These statistics, along with general information about the data, are going to be submitted in the next step.

## 2. Submit your data information

Note that you will be submitting general information about the data, not the data itself. The data never leaves your machine.

To submit your data information, you need to know the generated UID of your prepared dataset. Normally, you will see it in the output of the previous command. You can always check datasets information by running:

```
medperf dataset ls
```

You will find that the generated uid is `hashashash`.

Run the following command to submit your dataset information:

```
medperf dataset submit --data_uid hashashash
```

The information that is going to be submitted will be printed to the screen and you will be prompted to confirm that you want to submit.

Your dataset is successfully submitted! Next, request participation in the benchmark by initiating an association request.

## 3. Request Participation

In order to be able later on to submit results of executing a benchmark on your data, your data has to be associated with the benchmark.

To initiate an association request, you need to collect these information:

- The target benchmark ID, which is `1`
- The server UID of your data.

After you submitted your dataset to the server, it is assigned with a server UID. You can run `medperf dataset ls` again to find your dataset's server UID.

You will find that your dataset UID is `1`.

Run the following command to request associating your dataset with the benchmark:

```
medperf dataset associate --benchmark_uid 1 --data_uid 1
```

This command will first run the benchmark's reference model on your dataset to ensure your dataset is compatible with the workflow. After that, the association request information are printed to the screen, which includes execution summary of the test mentioned. You will be prompted to confirm sending these information and initiating this association request.

**What Happens After Requesting the Association?**

When you are participating with a real benchmark, you have to wait for the benchmark committee to approve the association request.

For the sake of continuing our tutorial only, run the following to simulate the benchmark committee approving your association:

```
medperf login --username=testbenchmarkowner --password=test
medperf association approve -b 1 -d 1
medperf login --username=testdataowner --password=test
```

## 4. Execute the Benchmark

It is time to run the benchmark! We provide a command that runs all models associated with a benchmark. To do that all you need is:

- The target benchmark ID, which is `1`
- The server UID of your data, which is `1`

Run the following command:

```
medperf benchmark run --benchmark 1 --data_uid 1
```

You will see at the end a summary of the executions. In our case, you will see something similar to the following:

TODO output

This means that the benchmark has two models:

- A model that you already have run when you requested the association. This explains why it was skipped.
- Another model which ran successfully. Its result generated UID is `b1m2d1`.

You can view the results by their UID. For example:

```
medperf result view b1m2d1
```

For now, your results are only local. Next, you will learn how to submit the results.

## 5. Submit a Result

We are going now to submit a result to the MedPerf server. To do so, you have to find the target result generated UID.

We will be submitting the result of UID `b1m2d1`. Run the following command:

```
medperf result submit --result b1m2d1
```

The information that is going to be submitted will be printed to the screen and you will be prompted to confirm that you want to submit.

## Cleanup (Optional)

You have reached the end of the tutorial! If you are planning to rerun any of our tutorials, don't forget to cleanup:

- To shut down the server: press `CTRL`+`C` in the terminal where the server is running.

- To cleanup the downloaded mock dataset:

```
rm -fr /tmp/medperf_test_files
```

- To cleanup the server database: (make sure you are in the MedPerf's root directory)

```
cd server
sh reset_db.sh
```

- To cleanup the test storage:

```
rm -fr ~/.medperf/localhost_8000
```
