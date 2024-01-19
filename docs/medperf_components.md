# MedPerf Components

![architecture](assets/components.png)

## MedPerf Server

The server contains all the metadata necessary to coordinate and execute experiments. No code assets or datasets are stored on the server.

The backend server is implemented in Django, and it can be found in the [server folder](https://github.com/mlcommons/medperf/tree/main/server){target="\_blank"} in the MedPerf Github repository.

## MedPerf Client

The MedPerf client contains all the necessary tools to interact with the server, preparing datasets for benchmarks and running experiments on the local machine. It can be found in this [folder](https://github.com/mlcommons/medperf/tree/main/cli/medperf){target="\_blank"} in the MedPerf Github repository.

The client communicates to the server through the API to, for example, authenticate a user, retrieve benchmarks/MLcubes and send results.

The client is currently available to the user through a command-line interface (CLI). <!--TODO: uncomment once cli_reference is filled. See the [CLI reference](cli_reference.md).-->

## Auth Provider

The auth provider manages MedPerf users identities, authentication, and authorization to access the MedPerf server. Users will authenticate with the auth provider and authorize their MedPerf client to access the MedPerf server. Upon authorization, the MedPerf client will use access tokens issued by the auth provider in every request to the MedPerf server. The MedPerf server is configured to processes only requests authorized by the auth provider.

Currently, MedPerf uses Auth0 as the auth provider.
