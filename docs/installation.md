## Prerequisites

#### Python

Make sure you have [Python 3.9](https://www.python.org/downloads/) installed along with [pip](https://pip.pypa.io/en/stable/installation/). To check if they are installed, run:

```
python --version
pip --version
```

or, depending on you machine configuration:

```
python3 --version
pip3 --version
```

We will assume the commands' names are `pip` and `python`. Use `pip3` and `python3` if your machine is configured differently.

#### Docker or Sinularity

Make sure you have the latest version of [Docker](https://docs.docker.com/get-docker/) or [Singularity 3.10](https://docs.sylabs.io/guides/3.0/user-guide/installation.html) installed.

To verify docker is installed, run:

```
docker --version
```

To verify singularity is installed, run:

```
singularity --version
```

If using Docker, make sure [you can run Docker as a non-root user](https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user)

## Install MedPerf

1. (Optional) MedPerf is better to be installed in a virtual environment like Anaconda (link). Having anaconda installed, create a virtual environment `medperf-env` with the following command:

```
conda create -n medperf-env python=3.9
```

2. Clone the MedPerf repository:

```
git clone https://github.com/mlcommons/medperf.git
cd medperf
```

3. Install MedPerf package:

```
pip install cli
```

4. Verify the installation:

```
medperf --version
```
