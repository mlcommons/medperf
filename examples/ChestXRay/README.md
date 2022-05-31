# Chest X-Ray Benchmark

This example contains the MLCubes used for the X-Ray Benchmark experiment. It provides the following MLCubes:
- [`chexpert_prep`](./chexpert_prep/): Data Preparator MLCube for preprocessing and standardizing the input data.
- [`xrv_chex_densenet`](./xrv_chex_densenet/): Pretrained Densenet model for chest X-Ray pathology detection.
- [`metrics`](./metrics/): Evaluator MLCube for computing metrics results on model predictions.