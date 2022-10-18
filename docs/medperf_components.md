# MedPerf Main Components 

MedPerf is currently composed of two main components:

## MedPerf Server 

The server contains all the metadata necessary to coordinate and execute experiments. No code assets or datasets are stored on the server.

The backend server is implemented in Django, and it can be found in the [server folder](https://github.com/mlcommons/medperf/tree/docs/server) in the MedPerf Github repository. 

## MedPerf Command-Line Interface (CLI) 

A command-line interface (CLI) is a text-based user interface (UI) used to run programs, manage files and interact with the computer. 

The MedPerf CLI contains all the necessary tools to interact with the server, preparing datasets for benchmarks and running experiments on the local machine. It can be found in the [cli folder](https://github.com/mlcommons/medperf/tree/docs/cli) in the MedPerf Github repository. 

The CLI communicates to the server through the API to, for example, authenticate a user, retrieve benchmarks/MLcubes and send results.
