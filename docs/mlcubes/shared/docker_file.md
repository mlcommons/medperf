#### project/Dockerfile

MLCubes rely on containers to work. By default, Medperf provides a functional Dockerfile, which uses `ubuntu:18.0.4` and `python3.6`. This Dockerfile handles all the required procedures to install your project and redirect commands to the `project/mlcube.py` file. You can modify as you see fit, as long as the entry point behaves as a CLI, as described before.

!!! note "Running Docker MLCubes with Singularity"
    If you are building a Docker MLCube and expect it to be also run using Singularity, you need to keep in mind that Singularity containers built from Docker images [ignore the `WORKDIR` instruction](https://github.com/apptainer/singularity/issues/380) if used in Dockerfiles. Make sure you also follow their [best practices for writing Singularity-compatible Dockerfiles](https://docs.sylabs.io/guides/3.10/user-guide/singularity_and_docker.html#best-practices-for-docker-singularityce-compatibility).
