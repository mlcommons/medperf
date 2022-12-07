# General Instructions 

## Installing MedPerf Dependencies

MedPerf has some dependencies that must be installed by the user before being able to run it, including [MLCube ](mlcubes.md#medperf-mlcubes)and the required runners (right now there are Docker and Singularity runners). Use the following command to install the dependencies:

```
pip install mlcube mlcube-docker mlcube-singularity
```

Depending on the runner you are going to use, you also need to download the runner engine. 

## Hosting the Server

To host the server, please follow the instructions inside the <code>[server/README.md](https://github.com/mlcommons/medperf/blob/main/server/README.md)</code> file.

## Installing the CLI

To install the CLI, please follow the instructions inside the <code>[cli/README.md](https://github.com/mlcommons/medperf/blob/main/cli/README.md)</code> file.

## Creating a User

After installing everything you need to run MedPerf, the first step to joining the platform is to create a user, which is done by the MedPerf administrator. If you haven’t received your credentials to access MedPerf, get in touch with the team.

After you get your credentials and server URL, you can log in to MedPerf using your credentials with the following command:

```
medperf login
```

You can also modify MedPerf’s `cli/medperf/config.py` file so it points to the development server (`server` variable) and you don’t need to provide additional arguments on runtime. For example, if you are running a server instance somewhere different from what the CLI expects, it might be better to modify the configuration file so that you don't need to write `--host=&lt;SERVER_URL>` with every command.

However, if you don’t want to change the configuration file, you can run every MedPerf command with <code>medperf <strong>--host</strong>=&lt;SERVER_URL></code>.
