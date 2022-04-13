# MedPerf-Study

This repo consists of 5 mlcubes:
* 1 data preparation cube
* 3 model cubes
* 1 metrics cube 

## Data Preparation

The data preparation cube includes processing for the following two dataset:
* https://www.synapse.org/#!Synapse:syn3193805/files/
* https://wiki.cancerimagingarchive.net/display/Public/Pancreas-CT

Generally, this cube converts CT scans to 512 x 512 images for 2.5D UNET segmentation models. 

## Model 

Each model cube contains a unique UNET model, based on the following sources:
* https://github.com/PacktPublishing/Modern-Computer-Vision-with-PyTorch/blob/master/Chapter09/Semantic_Segmentation_with_U_Net.ipynb
* https://docs.monai.io/en/stable/_modules/monai/networks/nets/unetr.html
* https://docs.monai.io/en/stable/_modules/monai/networks/nets/basic_unet.html

## Metrics

The metrics cube processes these predictions and outputs DICE scores and loss for the segmented pancreas. 
