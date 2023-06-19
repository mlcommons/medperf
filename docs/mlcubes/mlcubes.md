# MedPerf MLCubes

MLCube is a set of common conventions for creating Machine Learning (ML) software that can "plug-and-play" on many different systems. **It is basically a container image with a simple interface and the correct metadata** that allows researchers and developers to easily share and experiment with ML pipelines.

You can read more about MLCubes [here](https://mlcommons.org/en/mlcube/).

In MedPerf, MLCubes are required for creating the three technical components of a benchmarking experiment: the data preparation flow, the model inference flow, and the evaluation flow. A [Benchmark Committee](../roles.md#benchmark-committee) will be required to create three MLCubes that these components. A [Model Owner](../roles.md#model-owners) will be required to wrap their model code within an MLCube in order to submit it to the MedPerf server and participate in a benchmark.

MLCubes are general-purpose. MedPerf defines three specific design types of MLCubes according to their purpose: The **Data Preparator MLCube**, **the Model MLCube**, and the **Metrics MLCube**. Each type has a specific [MLCube task configuration](https://mlcommons.github.io/mlcube/getting-started/concepts/#task) that defines the MLCube's interface. Users need to follow these design specs when building their MLCubes to be conforming with MedPerf. We provide below a high-level description of each MLCube type and a link to a guide for building an example for each type.

## Data Preparator MLCube

The Data Preparator MLCube is used to prepare the data for executing the benchmark. Ideally, it can receive different data standards for the task at hand, transforming them into a single, unified standard. Additionally, it ensures the quality and compatibility of the data and computes statistics and metadata for registration purposes.

This MLCube's interface should expose the following tasks:

- **Prepare:** Transforms the input data into the expected output data standard. It receives as input the location of the original data, as well as the location of the labels, and outputs the prepared dataset and accompanying labels.

- **Sanity check:** Ensures the integrity of the prepared data. It may check for anomalies and data corruption (e.g. blank images, empty test cases). It constitutes a set of conditions the prepared data should comply with.

- **Statistics:** Computes statistics on the prepared data.

Check [this guide](mlcube_data.md) on how to create a Data Preparation MLCube.

## Model MLCube

The model MLCube contains a pre-trained machine learning model that is going to be evaluated by the benchmark. It's interface should expose the following task:

- **Infer:** Obtains predictions on the prepared data. It receives as input the location of the prepared data and outputs the predictions.

Check [this guide](mlcube_models.md) on how to create a Model MLCube.

## Metrics/Evaluator MLCube

The Metrics MLCube is used for computing metrics on the model predictions by comparing them against the provided labels. It's interface should expose the following task:

- **Evaluate:** Computes the metrics. It receives as input the location of the predictions and the location of the prepared data labels and generates a yaml file containing the metrics.

Check [this guide](mlcube_metrics.md) on how to create a Metrics MLCube.
