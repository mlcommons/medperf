# How to deploy MLCubes

Once you have an MLCube ready for medperf, you need to deploy it so that it can be identified and retrieved by other medperf users. This requires hosting the mlcube components somewhere on the cloud. The following is a description of what needs to be deployed and how Medperf expects this deployment to work.

## Components to be deployed

The following is the list of components that must be hosted separately so they can be used by MedPerf:

### `mlcube.yaml`
Every MLCube is defined by its `mlcube.yaml` manifest file. As such, Medperf needs to have access to this file to recreate the MLCube. This file can be found inside your MLCube at `<path_to_mlcube>/mlcube.yaml`.

### `parameters.yaml`
The `parameters.yaml` file specify additional ways to parametrize your model. Even if this file is not being used by your MLCube, medperf needs it to diferentiate between similar models with different parameters. This file can be found inside your MLCube at `<path_to_mlcube>/workspace/parameters.yaml`.

### `additional_files.tar.gz` (Optional)
MLCubes may require additional files that may be desired to keep separate from the model architecture and hosted image. For example, model weights. This allows for testing multiple implementations of the same model, without requiring a separate container image for each. If additional images are being used by your MLCube, they need to be compressed into a `.tar.gz` file and hosted separately. You can create this tarball file with the following command
```
tar -czf additional_files.tar.gz -C <path_to_mlcube>/workspace/additional_files .
```

### `image.tar.gz` (Optional)
MLCubes execute a container image behind the scenes. This container image is usually hosted on a container registry, like docker hub. In cases where this is not possible, medperf provides the option of passing the image as a `.tar.gz` file. MLCubes that work with images outside of the docker registry usually store the image inside the `<path_to_mlcube>/workspace/.image` folder. In those cases, you can run the following command to create the tarball file
```
tar -czf image.tar.gz -C <path_to_mlcube>/workspace/.image .
```

## Cloud hosting
In order for Medperf users to retrieve and use your MLCubes, assests must be hosted separately and publicly. This can be done with any cloud hosting tool/provider you desire (such as GCP, AWS, Dropbox, Google Drive, Github). As long as your files can be accessed through an HTTP `GET` method, it should work with medperf. You can see if your files are hosted correctly by running
```
wget <asset_url>
```
If the file gets downloaded correctly just by using this command, then your hosting is compatible with Medperf.

## Synapse hosting
We provide the option of hosting with synapse, in cases where privacy is a concern. Synapse provides both data storage and a container registry with well established data governance and sharing rules. Please refer to the following resources for file and docker submission to the Synapse platform:

- [Synapse: Uploading and Organizing Data Into Projects, Files and Folders](https://help.synapse.org/docs/Uploading-and-Organizing-Data-Into-Projects,-Files,-and-Folders.2048327716.html)
- [Synapse: Docker Registry](https://help.synapse.org/docs/Synapse-Docker-Registry.2011037752.html)

!!! note
    When using the Synapse Docker Registry, make sure to also update the docker image name in your `mlcube.yaml` so it points to the Synapse Registry.

## Preparing an MLCube for deployment
To facilitate hosting, we have provided a script that finds all the required assets, compresses them if necessary, and places them in a single location for easy access. To run it, you should:

1. Clone medperf repository
   ```
   git clone https://github.com/mlcommons/medperf
   cd medperf
   ```
2. execute script with your MLCube
   ```
   python scripts/package-mlcube.py path/to/mlcube --output path/to/file.tar.gz
   ```
   where `path/to/mlcube` is the path to the folder containing `mlcube.yaml` and `workspace`, and `path/to/file.tar.gz` is a path to the output file where you want to store the compressed version of all assets.

Once executed, you should be able to find all prepared assets at `./mlcube/deploy`, as well as a compressed version of the `deploy` folder at the output path provided.

!!! note
    The `--output` parameter is optional. The compressed version of the `deploy` folder can be useful in cases where you don't directly interact with the medperf server, but instead you do so through a third party. This is usually the cases for challenges and competitions.