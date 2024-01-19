## Before You Start

#### First steps

##### Running in cloud via Github Codespaces

As the most easy way to play with the tutorials you can launch a preinstalled [Codespace](https://github.com/features/codespaces) cloud environment for MedPerf by clicking this link: 

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=416800365)

##### Running in local environment

To start experimenting with MedPerf through this tutorial on your local machine, you need to start by following these quick steps:

  1. **[Install Medperf](../installation)**
  2. **[Set up Medperf](../setup)**

#### Prepare the Local MedPerf Server

For the purpose of the tutorial, you have to initialize a local MedPerf server with a fresh database and then create the necessary entities that you will be interacting with. To do so, run the following: (make sure you are in MedPerf's root folder)

```bash
cd server
sh reset_db.sh
python seed.py --demo {{page.meta.tutorial_id}}
cd ..
```

#### Download the Necessary files

A script is provided to download all the necessary files so that you follow the tutorial smoothly. Run the following: (make sure you are in MedPerf's root folder)

```bash
sh tutorials_scripts/setup_{{page.meta.tutorial_id}}_tutorial.sh
```

This will create a workspace folder `medperf_tutorial` where all necessary files are downloaded. The folder contains the following content:

<details markdown>
<summary>Toy content description</summary>
{% include "getting_started/shared/tutorials_content_overview/"+page.meta.tutorial_id+".md" %}
</details>

In real life all the listed artifacts and files have to be created on your own. However, for tutorial's sake you may use this toy data.   

#### Login to the Local MedPerf Server

The local MedPerf server is pre-configured with a dummy local authentication system. Remember that when you are communicating with the real MedPerf server, you should follow the steps in [this guide](../concepts/auth.md#login) to login. For the tutorials, you should not do anything.

You are now ready to start!
