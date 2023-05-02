#### project/Dockerfile

MLCubes rely on containers to work. By default, Medperf provides a functional Dockerfile, which uses `ubuntu:18.0.4` and `python3.6`. This Dockerfile handles all the required procedures to install your project and redirect commands to the `project/mlcube.py` file. You can modify as you see fit, as long as the entry point behaves as a CLI, as described before.

!!! warning
    If you are building a Docker MLCube and expect it to be also run using Singularity, you need to keep in mind that Singularity containers built from Docker images [ignore the `WORKDIR` instructions]() used in their Dockerfiles, and use the user's home directory as the working directory by default. So if you want the MLCube to be run with both Docker and Singularity, make sure you don't assume a fixed working directory when writing your Dockerfile. A solution that always works is to consistently use either relative paths or absolute paths, not both.
