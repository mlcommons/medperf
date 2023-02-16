Before proceeding, make sure you have the [MedPerf client installed.](../installation.md)

This set of tutorials will cover the basic usage of MedPerf. We will present a guided walkthrough of a simple benchmarking scenario through an example.
The example will simulate benchmarking the task of chest-Xray classification (...describe). It will involve the roles of the three entities of interest:

- **The benchmark committee:** This will simulate a user that wants to kick-off a benchmark on Chest-Xray classification. Their main actions involve defining, creating, and submitting the benchmark, as well as managing experiments (e.g. approve which datasets and models can participate)
- **The model owner:** This will simulate a researcher that wants to test the performance of their deep learning model (a ResNet model) on chest-Xray classification. Their main actions involve submitting a model MLCube and requesting participation in the benchmark.
- **The data owner:** This will simulate a hospital that has raw chest-Xray data and wants to allow testing deep learning models on their data while keeping it private. Their main actions involve preparing the data, submitting the metadata of the prepared dataset, requesting participation in the benchmark, execute the benchmark models on the prepared dataset, and submitting the results of the execution.

First, you have to [set up](setup.md) the general testing environment. Then, depending on how you are going to use MedPerf, we provide the following hands-on tutorials:

- [How a benchmark committee can create and submit a benchmark.](benchmark_owner_demo.md)

- [How a model owner can submit a model.](model_owner_demo.md)

- [How a data owner can prepare their data and execute a benchmark.](data_owner_demo.md)

For a detailed reference on the commands used throughout the tutorials, you can always refer to the command line interface documentation (TODO: link).
