# MedPerf MLCubes 

MLCube is a set of common conventions for creating ML software that can "plug-and-play" on many different systems. **It is basically a container image with a simple interface and the correct metadata** that allows anyone who receives the ML model to run it on their local machine, Google Cloud Platform (GCP), etc. 

**Note:** A Docker container image is a lightweight, executable package of software that includes everything needed to run an application, and this container needs to conform to one of the MedPerf interfaces for data preparation, ML models, or evaluation metrics.

You can get started with MLCube [here](https://mlcommons.org/en/mlcube/).

In MedPerf, MLCubes are required for creating benchmarks. A Benchmark Committee will require three cubes to be submitted to the platform before creating a benchmark: **Data Preparator MLCube, Reference Model MLCube** and **Metrics MLCube.**

The steps to build each of these cubes can be found [here](https://github.com/aristizabal95/mlcube_examples/tree/medperf-examples/medperf).

## Data Preparator MLCube 

The Data Preparator MLCube is used to prepare the data for executing the benchmark. Ideally, it can receive different data standards for the task at hand, transforming them into a single, unified standard. Additionally, it ensures the quality and compatibility of the data and computes statistics and metadata for registration purposes. 

This MLCube provides the following tasks:

**Prepare:** Transforms the input data into the expected output data standard. It receives as input the location of the original data, as well as the location of the labels, and outputs the prepared dataset and accompanying labels.

**Sanity check:** Ensures data integrity of the prepared data. It ideally checks for anomalies and data corruption (e.g. blank images, empty test cases). It constitutes a set of conditions the prepared data should comply with.

**Statistics:** Computes statistics on the prepared data. These statistics are displayed to the user and, if given consent, uploaded to the server for dataset registration. An example is shown as follows:

```
generated_metadata:
  column statistics:
    Atelectasis:
      '0.0': 0.625
      '1.0': 0.375
    Cardiomegaly:
      '0.0': 0.67
      '1.0': 0.33
    Consolidation:
      '0.0': 0.84
      '1.0': 0.16
    Edema:
      '0.0': 0.79
      '1.0': 0.21
  images statistics:
    channels: 1
    height:
      max: 224.0
      mean: 224.0
      min: 224.0
      std: 0.0
    pixels_max:
      max: 255.0
      mean: 255.0
      min: 255.0
      std: 0.0
    pixels_mean:
      max: 149.2486049107
      mean: 137.7983645568
      min: 121.2493223852
      std: 5.8131783153
    pixels_min:
      max: 6.0
      mean: 0.07
      min: 0.0
      std: 0.5063416925
    pixels_std:
      max: 79.0369075709
      mean: 71.5894559861
      min: 64.0834766712
      std: 2.8957115261
    width:
      max: 224.0
      mean: 224.0
      min: 224.0
      std: 0.0
  labels:
  - Atelectasis
  - Cardiomegaly
  - Consolidation
  - Edema
  size: 200
```

## Model MLCube 

The model MLCube contains a pre-trained machine learning model that is going to be evaluated by the benchmark. It provides the following task:

**Infer:** Obtains predictions on the prepared data. It receives as input the location of the prepared data and outputs predictions.

## Metrics/Evaluator MLCube 

The Metrics MLCube is used for computing metrics on the model predictions by comparing it against the provided labels. It provides the following task:

**Evaluate:** Computes the metrics. It receives as input the location of the predictions and the location of the prepared data (which contains the labels) and generates a yaml file with the metrics.

Both the Model and Metrics MLCubes can be executed independently if given the correct inputs. Medperf provides a single command for both obtaining predictions and computing metrics on an already prepared dataset.
