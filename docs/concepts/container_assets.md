# Container Assets: What to Host?

Once you have built a container ready for MedPerf, you need to host its assets somewhere on the cloud so that it can be identified and retrieved by the MedPerf client on other machines. This requires hosting the container components somewhere on the cloud. The following is a description of what needs to be hosted.

## Hosting Your Container Image

The container image should be hosted in a container registry, like Docker Hub. For singularity, medperf provides the option of passing the URL of a .sif image file directly (i.e. having the [image file hosted somewhere](hosting_files.md) and providing MedPerf with the download link).

!!! note Note 1
    While there is the option of hosting the singularity image directly, it is highly recommended to use a container registry for accessability and usability purposes. MedPerf also has mechanisms for converting containers for other container runners, like Docker to Singularity.

!!! note Note 2
    Docker Images can be on any docker container registry, not necessarily on Docker Hub.

## Files to be hosted

The following is the list of files that must be hosted separately so they can be used by MedPerf:

### `container_config.yaml`

Every container is defined by its [`container_config.yaml`](../containers/containers.md#container-configuration-files) manifest file. As such, Medperf needs to have access to this file to use the container.

### `parameters.yaml` (Optional)

If your container depends on a parameters file (see [here](../containers/containers.md#extra-mounts)), the `parameters.yaml` file needs to be hosted as well and its URL should be provided to the container submission command.

### `additional_files.tar.gz` (Optional)

If your container depends on additional files (see [here](../containers/containers.md#extra-mounts)), the `additional_files.tar.gz` file needs to be hosted as well and its URL should be provided to the container submission command. Here is how this file should be compressed in order for MedPerf to be able to decompress it and mount it to your container during runtime:

Suppose you have your additional files inside a folder named `additional_files`. Then, compress this folder using the following command:

```bash
tar -czf additional_files.tar.gz -C <path_to_the_additional_files_folder> .
```

This will create the `additional_files.tar.gz` archive that can then be hosted and its URL should be provided to the container submission command.

## See Also

- [File Hosting](hosting_files.md)
