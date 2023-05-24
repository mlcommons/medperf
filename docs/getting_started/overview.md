# Overview

In this getting started section, you will understand the fundamentals of MedPerf through a straightforward benchmarking example, which involves the simulation of a chest X-rays classification process. 

First of all, you will learn about the roles of three key entities involved in this scenario, including:  

- **Benchmark Committee:** The Benchmark Commitee will simulate a user that wants to kick off a benchmark on Chest X-ray classification. Their main actions involve defining, creating, and submitting the benchmark, as well as managing experiments (e.g., approving which datasets and models will be allowed to participate)
- **Model Owner:** The Model Owner will simulate a researcher who wants to test the performance of their deep learning (a ResNet model) on chest-Xray classification. The main actions of this entity involve submitting a model MLCube and requesting participation in the benchmark.
- **Data Owner:** The Data Owner will simulate a hospital that has a raw chest X-ray data and wants to allow testing deep learning models on their data while keeping it private. The main actions of this entity involve preparing the data, submitting the metadata of the prepared dataset, requesting participation in the benchmark, executing the benchmark models on the prepared dataset, and submitting the results of the execution.

Before proceeding, make sure you have the [MedPerf client installed](../installation.md) and the general testing environment [set up](setup.md). The following list provides useful links to hands-on tutorials that can help you get started with MedPerf:

- [How a benchmark committee can create and submit a benchmark.](benchmark_owner_demo.md)

- [How a model owner can submit a model.](model_owner_demo.md)

- [How a data owner can prepare their data and execute a benchmark.](data_owner_demo.md)

For a detailed reference on the commands used throughout the tutorials, you can always refer to the [command line interface documentation](../cli_reference.md).
