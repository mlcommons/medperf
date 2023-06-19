# Pancreas Segmentation MLCubes

**(This example is currently not compatible with the latest MedPerf version. This will be fixed soon)**

This contains the code for the MLCubes related to Pancreas Segmentation that took place acroos Dana-Farber Cancer Institute and Harvard T.H. Chan School of Public Health.

There are 3 MLCubes:

### prep: Data Preparation MLCube
Our Data Preparation MLCube reads the raw CT data, performs the necessary preprocessing steps, and saves the outputs as numpy arrays. 3D volumes of abdominal CT scans can have different spatial orientation based on the type of acquisition tool used and how it was placed. The MLCube we built applies a set of preprocessing steps (rotations, scaling) to the BTCV volumes to become aligned with the TCIA volumes. For the labels, the MLCube supports NIfTI data format. Since the BTCV dataset is a multi-organ dataset, its labels were altered such that all organs other than the pancreas are regarded as background.

### model: Model MLCube

The Model MLCube implements an RSTN model for pancreas segmentation whose codebase is available both in PyTorch (https://github.com/twni2016/OrganSegRSTN_PyTorch) and Caffe2 (https://github.com/198808xc/OrganSegRSTN). The PyTorch model version was trained on the TCIA dataset, on patients subjects of IDs 21 to 82 (60 subjects), as described in their GitHub repository: https://github.com/twni2016/OrganSegRSTN_PyTorch#5-pre-trained-models-on-the-nih-dataset. We used the pretrained model weights they publicly provide. Inference in this model consists of two stages: a coarse stage, where inference is done on each 2D slice of the three possible planar views, and a fine stage, where the previous predictions are fused together and processed. The MLCube implements both stages and saves all the predictions as compressed numpy arrays in a unified structure ready for evaluation.

### metrics: Metrics MLCube
Metrics MLCube evaluates the output segmentations generated from the model MLCube and produces results using the metrics of interest. The Sørensen–Dice coefficient (DSC) was the metric used for evaluating the output segmentations.
