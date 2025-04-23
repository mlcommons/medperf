# Setup

This setup is only for running the tutorials. If you are using MedPerf with a real benchmark and real experiments, skip to [this section](#choose-the-container-runner) to optionally change your container runner. Then, follow the tutorials as a general guidance for your real experiments.

## Install the MedPerf Client

If this is your first time using MedPerf, install the MedPerf client library as described [here](installation.md).  

## Run a Local MedPerf Server

For this tutorial, you should spawn a local MedPerf server for the MedPerf client to communicate with. Note that this server will be hosted on your `localhost` and not on the internet.

1. Install the server requirements ensuring you are in MedPerf's root folder. If a virtual environment was created when installing the MedPerf client (see [this section](installation.md#install-medperf)), make sure the same virtual environment is used when installing the local server dependencies:

    ```bash
    pip install -r server/requirements.txt
    pip install -r server/test-requirements.txt
    ```

2. Run the local MedPerf server using the following command:

    ```bash
    cd server
    cp .env.local.local-auth.sqlite .env
    sh setup-dev-server.sh
    ```

The local MedPerf server now is ready to recieve requests. You can always stop the server by pressing `CTRL`+`C` in the terminal where you ran the server.

After that, you will be configuring the MedPerf client to communicate with the local MedPerf server. Make sure you continue following the instructions in a new terminal.

## Configure the MedPerf Client

<!-- TODO: set links to ["`profiles`"](../concepts/profiles.md) once profiles are filled -->
The MedPerf client can be configured by creating or modifying "`profiles`". A profile is a set of configuration parameters used by the client during runtime. By default, the profile named `default` will be active.

The `default` profile is preconfigured so that the client communicates with the main MedPerf server ([api.medperf.org](https://api.medperf.org){target="\_blank"}). For the purposes of the tutorial, you will be using the `local` profile as it is preconfigured so that the client communicates with the local MedPerf server.

To activate the `local` profile, run the following command:

```bash
medperf profile activate local
```

You can always check which profile is active by running:

```bash
medperf profile ls
```

To view the current active profile's configured parameters, you can run the following:

```bash
medperf profile view
```

#### Choose the Container Runner

You can configure the MedPerf client to use either Docker or Singularity. The `local` profile is configured to use Docker. If you want to use MedPerf with Singularity, modify the `local` profile configured parameters by running the following:

```bash
medperf profile set --platform singularity
```

This command will modify the `platform` parameter of the currently activated profile.

## What's Next?

The local MedPerf server now is ready to recieve requests, and the MedPerf client is ready to communicate. Depending on your role, you can follow these hands-on tutorials:

- [How a benchmark committee can create and submit a benchmark.](benchmark_owner_demo.md)

- [How a model owner can submit a model.](model_owner_demo.md)

- [How a data owner can prepare their data and execute a benchmark.](data_owner_demo.md)
