## Before You Start

#### Prepare the Local MedPerf Server

For the purpose of the tutorial, you have to initialize a local MedPerf server with a fresh database and then create the necessary entities that you will be interacting with. To do so, run the following: (make sure you are in MedPerf's root folder)

```bash
cd server
sh reset_db.sh
python populate_for_tutorials.py --demo {{page.meta.tutorial_id}}
cd ..
```

#### Download the Necessary files

A script is provided to download all the necessary files so that you follow the tutorial smoothly. Run the following: (make sure you are in MedPerf's root folder)

```bash
sh tutorials_scripts/setup_{{page.meta.tutorial_id}}_tutorial.sh
```

This will create a workspace folder `medperf_tutorial` where all necessary files are downloaded.

#### Login to the Local MedPerf Server

Run the command below and follow the instructions printed on the screen:

```bash
medperf auth login
```

For more details about how to login, check [this guide](../concepts/auth.md#login)

You are now ready to start!
