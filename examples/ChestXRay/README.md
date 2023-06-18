# Chest X-Ray Benchmark

**(This example is currently not compatible with the latest MedPerf version. This will be fixed soon)**

This example contains the MLCubes used for the X-Ray Benchmark experiment. It provides the following MLCubes:

- [`chexpert_prep`](./chexpert_prep/): Data Preparator MLCube for preprocessing and standardizing the input data.
- [`xrv_densenet`](./xrv_densenet/): Pretrained Densenet model for chest X-Ray pathology detection.
- [`metrics`](./metrics/): Evaluator MLCube for computing metrics results on model predictions.
