# How to run tests

1. Download and extract (sha256: 701fbba8b253fc5b2f54660837c493a38dec986df9bdbf3d97f07c8bc276a965):
<https://storage.googleapis.com/medperf-storage/rano_test_assets/dev.tar.gz>

2. Move `additional_files` and `input_data` to the mlcube workspace
3. Move `tmpmodel` and `atlasImage_0.125.nii.gz` to the mlcube project folder

4. Build the base docker image from the repo's root folder Dockerfile
5. Build the dev docker image using `Dockerfile.dev` in the mlcube project folder.
6. Then change the docker image name in `mlcube.yaml` according to step 5.
7. Then go to `mlcube` folder and run the tests scripts
