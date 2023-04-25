# Create a workspace
mkdir -p medperf_tutorial
cd medperf_tutorial

# Download the data
wget https://upenn.box.com/shared/static/y8162xkq1zz5555ye3pwadry2m2e39bs.zip
unzip y8162xkq1zz5555ye3pwadry2m2e39bs.zip
mv data/2d_rad_segmentation .
rm y8162xkq1zz5555ye3pwadry2m2e39bs.zip
rm -rf data

# Setup the data CSV
echo "SubjectID,Channel_0,Label,ValueToPredict
001,2d_rad_segmentation/001/image.png,2d_rad_segmentation/001/mask.png
002,2d_rad_segmentation/002/image.png,2d_rad_segmentation/002/mask.png
003,2d_rad_segmentation/003/image.png,2d_rad_segmentation/003/mask.png
004,2d_rad_segmentation/004/image.png,2d_rad_segmentation/004/mask.png
005,2d_rad_segmentation/005/image.png,2d_rad_segmentation/005/mask.png
006,2d_rad_segmentation/006/image.png,2d_rad_segmentation/006/mask.png
007,2d_rad_segmentation/007/image.png,2d_rad_segmentation/007/mask.png
008,2d_rad_segmentation/008/image.png,2d_rad_segmentation/008/mask.png
009,2d_rad_segmentation/009/image.png,2d_rad_segmentation/009/mask.png
010,2d_rad_segmentation/010/image.png,2d_rad_segmentation/010/mask.png" >> inputs.csv

# Setup config file and medperf_mlcube file
git clone https://github.com/mlcommons/GaNDLF.git
mv GaNDLF/samples/config_classification.yaml config_classification.yaml
rm -rf GaNDLF
