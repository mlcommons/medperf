# MedPerf Components

MedPerf is composed of software pieces:

## MedPerf Server

The server contains all the metadata necessary to coordinate and execute experiments. No code assets or datasets are stored on the server.

The backend server is implemented in Django, and it can be found in the [server folder](https://github.com/mlcommons/medperf/tree/main/server){target="\_blank"} in the MedPerf Github repository.

## MedPerf Client

The MedPerf client contains all the necessary tools to interact with the server, preparing datasets for benchmarks and running experiments on the local machine. It can be found in this [folder](https://github.com/mlcommons/medperf/tree/main/cli/medperf){target="\_blank"} in the MedPerf Github repository.

The client communicates to the server through the API to, for example, authenticate a user, retrieve benchmarks/MLcubes and send results.

The client is currently available to the user through a command-line interface (CLI). See the [CLI reference](cli_reference.md).
