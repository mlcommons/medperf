# MLCube Components: What to Host?

Once you have built an MLCube ready for MedPerf, you need to host it somewhere on the cloud so that it can be identified and retrieved by the MedPerf client on other machines. This requires hosting the MLCube components somewhere on the cloud. The following is a description of what needs to be hosted.

## Hosting Your Container Image

MLCubes execute a container image behind the scenes. This container image is usually hosted on a container registry, like Docker Hub. In cases where this is not possible, medperf provides the option of passing the image file directly (i.e. having the [image file hosted somewhere](hosting_files.md) and providing MedPerf with the download link). MLCubes that work with images outside of the docker registry usually store the image inside the `<path_to_mlcube>/workspace/.image` folder. MedPerf supports using direct container image files **for Singularity only**.

!!! note Note 1
    While we provide the option of hosting the singularity image directly, we encourage using a container registry for accessability and usability purposes. MLCube also has mechanisms for converting containers to other runners, like Docker to Singularity.

!!! note Note 2
    Docker Images can be on any docker container registry, not necessarily on Docker Hub.

## Files to be hosted

The following is the list of files that must be hosted separately so they can be used by MedPerf:

### `mlcube.yaml`

Every MLCube is defined by its `mlcube.yaml` manifest file. As such, Medperf needs to have access to this file to recreate the MLCube. This file can be found inside your MLCube at `<path_to_mlcube>/mlcube.yaml`.

### `parameters.yaml` (Optional)

The `parameters.yaml` file specify additional ways to parametrize your model MLCube using the same container image it is built with. This file can be found inside your MLCube at `<path_to_mlcube>/workspace/parameters.yaml`.

### `additional_files.tar.gz` (Optional)

MLCubes may require additional files that may be desired to keep separate from the model architecture and hosted image. For example, model weights. This allows for testing multiple implementations of the same model, without requiring a separate container image for each. If additional images are being used by your MLCube, they need to be compressed into a `.tar.gz` file and hosted separately. You can create this tarball file with the following command

```bash
tar -czf additional_files.tar.gz -C <path_to_mlcube>/workspace/additional_files .
```

## Preparing an MLCube for hosting

To facilitate hosting and implementation validation, we provide a script that finds all the required assets, compresses them if necessary, and places them in a single location for easy access. To run the script, make sure you have [medperf installed](../installation.md) and you are in medperf's root directory:

```bash
python scripts/package-mlcube.py \
   --mlcube path/to/mlcube \
   --mlcube-types <list-of-comma-separated-strings> \
   --output path/to/file.tar.gz
```

where:

  - `path/to/mlcube` is the path to the MLCube folder containing the manifest file (`mlcube.yaml`)
  - `--mlcube-types` specifies a comma-separated list of MLCube types ('data-preparator' for a data preparation MLCube, 'model' for a model MLCube, and 'metrics' for a metrics MLCube.)
  - `path/to/file.tar.gz` is a path to the output file where you want to store the compressed version of all assets.

See `python scripts/package-mlcube.py --help` for more information.

Once executed, you should be able to find all prepared assets at `./mlcube/assets`, as well as a compressed version of the `assets` folder at the output path provided.

!!! note
    The `--output` parameter is optional. The compressed version of the `assets` folder can be useful in cases where you don't directly interact with the medperf server, but instead you do so through a third party. This is usually the case for challenges and competitions.

## See Also

- [File Hosting](hosting_files.md)
