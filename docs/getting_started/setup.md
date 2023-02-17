## Run a Local Server

For the purpose of the tutorials, you should spawn a local MedPerf server for the MedPerf client to communicate with. Note that this server will be hosted on your `localhost` and not to the internet.

1. Install the server requirements if you didn't before: (make sure you are in MedPerf's root folder)

```
pip install -r server/requirements.txt
```

2. Switch to the server directory and run the server:

```
cd server
sh setup_dev_server.sh
```

**Note**: If this is not the first time you run the local server, the server may still have data from previous client runs. If you want to spawn the server with a fresh database, you should run this instead of the above command: `sh setup_dev_server.sh -r 1`.

The local server now is ready to recieve requests. You can always stop the server by pressing `CTRL`+`C` in the terminal where you ran the server.

It's time now to configure the client to communicate with the local server.

## Configure the Client

The MedPerf client can be configured by creating or modifying "`profiles`". A profile is a set of configuration parameters used by the client during runtime. MedPerf comes with two already created profiles: the `default` and `test` profiles. The `default` profile is the active one by default, and is preconfigured so that the client communicates with the main MedPerf server ([api.medperf.org](api.medperf.org)). For the purposes of the tutorial, we will be using the `test` profile as it is preconfigured so that the client communicates with the local server.

To activate the `test` profile, run:

```
medperf profile activate test
```

You can always check which profile is active by running:

```
medperf profile ls
```

To view the current active profile's configured parameters, you can run the following:

```
medperf profile view
```

#### Choose the Container Runner

You can configure the client to use either Docker or Singularity. The `test` profile is configured to use Docker. If you want to run the tutorials with Singularity, run the following:

```
medperf profile set --platform singularity
```

This will modify the `platform` parameter of the currently activated profile.

## What's Next?

The local server now is ready to recieve requests, and the client is ready to communicate. Depending on how you want to use MedPerf, you can follow our hands-on tutorials:

- [How a benchmark committee can create and submit a benchmark.](benchmark_owner_demo.md)

- [How a model owner can submit a model.](model_owner_demo.md)

- [How a data owner can prepare their data and execute a benchmark.](data_owner_demo.md)
