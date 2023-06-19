# Overview

The MedPerf client provides all the necessary tools for a complete benchmark experiment. Below, you will find a comprehensive breakdown of user roles and the corresponding functionalities they can access and perform using the MedPerf client:

- **Benchmark Committee:** The [Benchmark Commitee](../roles.md#benchmark-committee) can define and create a benchmark, as well as manage experiments (e.g., approving which datasets and models will be allowed to participate)
- **Model Owner:** The [Model Owner](../roles.md#model-owners) can submit a model to the MedPerf server and request participation in a benchmark.
- **Data Owner:** The [Data Owner](../roles.md#data-providers) can prepare their raw medical data, register the **metadata** of their prepared dataset, request participation in a benchmark, execute a benchmark's models on their data, and submit the results of the execution.

To ensure users have the best experience in learning the fundamentals of MedPerf and utilizing the MedPerf client, the following set of tutorials are provided:

- [How a Benchmark Committee can create and submit a benchmark.](benchmark_owner_demo.md)

- [How a Model Owner can submit a model.](model_owner_demo.md)

- [How a Data Owner can prepare their data and execute a benchmark.](data_owner_demo.md)

The tutorials simulate a benchmarking example for the task of detecting thoracic diseases from chest X-ray scans. You can find the description of the used data [here](https://www.nih.gov/news-events/news-releases/nih-clinical-center-provides-one-largest-publicly-available-chest-x-ray-datasets-scientific-community). Throughout the tutorials, you will be interacting with a temporary local MedPerf server as described in the [setup page](setup.md). This allows you to freely experiment with the MedPerf client and rerun the tutorials as many times as you want, providing you with an immersive learning experience. Please note, however, that these tutorials also serve as a general guidance to be followed when using the MedPerf client in a real scenario.

Before proceeding to the tutorials, make sure you have the [MedPerf client installed](installation.md) and the general tutorial environment [set up](setup.md).

For a detailed reference on the commands used throughout the tutorials, you can always refer to the [command line interface documentation](../cli_reference.md).
