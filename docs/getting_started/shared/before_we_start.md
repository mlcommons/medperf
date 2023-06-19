## Before You Start

#### Prepare the Local MedPerf Server

For the purpose of the tutorial, you have to initialize a local MedPerf server with a fresh database and then create the necessary entities that you will be interacting with. To do so, run the following: (make sure you are in MedPerf's root folder)

```bash
cd server
sh reset_db.sh
python seed.py --cert cert.crt --demo {{page.meta.tutorial_id}}
cd ..
```

#### Download the Necessary files

A script is provided to download all the necessary files so that you follow the tutorial smoothly. Run the following: (make sure you are in MedPerf's root folder)

```bash
sh tutorials_scripts/setup_{{page.meta.tutorial_id}}_tutorial.sh
```

This will create a workspace folder `medperf_tutorial` where all necessary files are downloaded.

#### Login to the Local MedPerf Server

You credentials in this tutorial will be a username: `test{{page.meta.tutorial_id}}owner` and a password: `test`. Run:

```bash
medperf login
```

You will be prompted to enter your credentials.

You are now ready to start!
