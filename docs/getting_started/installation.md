# Installation

## Prerequisites

#### Python

Make sure you have [Python 3.9](https://www.python.org/downloads/){target="\_blank"} installed along with [pip](https://pip.pypa.io/en/stable/installation/){target="\_blank"}. To check if they are installed, run:

```bash
python --version
pip --version
```

or, depending on you machine configuration:

```bash
python3 --version
pip3 --version
```

We will assume the commands' names are `pip` and `python`. Use `pip3` and `python3` if your machine is configured differently.

#### Docker or Sinularity

Make sure you have the latest version of [Docker](https://docs.docker.com/get-docker/){target="\_blank"} or [Singularity 3.10](https://docs.sylabs.io/guides/3.0/user-guide/installation.html){target="\_blank"} installed.

To verify docker is installed, run:

```bash
docker --version
```

To verify singularity is installed, run:

```bash
singularity --version
```

If using Docker, make sure [you can run Docker as a non-root user.](https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user){target="\_blank"}

## Install MedPerf

1. (Optional) MedPerf is better to be installed in a virtual environment. We recommend using [Anaconda](https://docs.anaconda.com/anaconda/install/index.html){target="\_blank"}. Having anaconda installed, create a virtual environment `medperf-env` with the following command:

    ```bash
    conda create -n medperf-env python=3.9
    ```

    Then, activate your environment:

    ```bash
    conda activate medperf-env
    ```

2. Clone the MedPerf repository:

    ```bash
    git clone https://github.com/mlcommons/medperf.git
    cd medperf
    ```

3. Install MedPerf from source:

    ```bash
    pip install -e ./cli
    ```

4. Verify the installation:

    ```bash
    medperf --version
    ```

## What's Next?

Create your MedPerf account by following the instructions [here](signup.md).
