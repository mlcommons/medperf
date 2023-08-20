# Create a workspace
mkdir -p medperf_tutorial
cd medperf_tutorial

# Download the data
wget https://upenn.box.com/shared/static/y8162xkq1zz5555ye3pwadry2m2e39bs.zip
unzip y8162xkq1zz5555ye3pwadry2m2e39bs.zip
mv data/3d_rad_segmentation .
rm y8162xkq1zz5555ye3pwadry2m2e39bs.zip
rm -rf data

# Setup the data CSV
echo "SubjectID,Channel_0,Label
001,3d_rad_segmentation/001/image.nii.gz,3d_rad_segmentation/001/mask.nii.gz
002,3d_rad_segmentation/002/image.nii.gz,3d_rad_segmentation/002/mask.nii.gz
003,3d_rad_segmentation/003/image.nii.gz,3d_rad_segmentation/003/mask.nii.gz
004,3d_rad_segmentation/004/image.nii.gz,3d_rad_segmentation/004/mask.nii.gz
005,3d_rad_segmentation/005/image.nii.gz,3d_rad_segmentation/005/mask.nii.gz
006,3d_rad_segmentation/006/image.nii.gz,3d_rad_segmentation/006/mask.nii.gz
007,3d_rad_segmentation/007/image.nii.gz,3d_rad_segmentation/007/mask.nii.gz
008,3d_rad_segmentation/008/image.nii.gz,3d_rad_segmentation/008/mask.nii.gz
009,3d_rad_segmentation/009/image.nii.gz,3d_rad_segmentation/009/mask.nii.gz
010,3d_rad_segmentation/010/image.nii.gz,3d_rad_segmentation/010/mask.nii.gz" >> data.csv

# Setup config file
wget https://raw.githubusercontent.com/mlcommons/GaNDLF/master/samples/config_getting_started_segmentation_rad3d.yaml
