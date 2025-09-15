---
assets_url: https://raw.githubusercontent.com/mlcommons/medperf/main/examples/chestxray_tutorial/
hide:
  - toc
---


# Hands-on Tutorial for Federated Training with Nvidia Flare

{% set prep_container = assets_url+"data_preparator/container_config.yaml" %}
{% set train_container = assets_url+"data_preparator/container_config.yaml" %}
{% set admin_train_container = assets_url+"data_preparator/container_config.yaml" %}

## Overview

In this guide, you will learn how you can kick-off a training experiment with MedPerf.

The main tasks of this guide are:

1. Testing container compatibility with the benchmark.
2. Submitting the container.
3. Requesting participation in a benchmark.

It's assumed that you have already set up the general testing environment as explained in the [setup guide](setup.md).

## Before You Start

#### First steps

##### Running in local environment

To start experimenting with MedPerf through this tutorial on your local machine, you need to start by following these quick steps:

  1. **[Install Medperf](../installation)**
  2. **[Set up Medperf](../setup)**

#### Prepare the Local MedPerf Server

For the purpose of the tutorial, you have to initialize a local MedPerf server with a fresh database and then create the necessary entities that you will be interacting with. To do so, run the following: (make sure you are in MedPerf's root folder)

```bash
cd server
sh reset_db.sh
python seed.py --demo benchmark
cd ..
```

#### Download the Necessary files

A script is provided to download all the necessary files so that you follow the tutorial smoothly. Run the following: (make sure you are in MedPerf's root folder)

```bash
sh tutorials_scripts/setup_training_tutorial.sh
```

This will create a workspace folder `medperf_tutorial` where all necessary files are downloaded. The folder contains the following content:

<details markdown>
<summary>Toy content description</summary>
{% include "getting_started/shared/tutorials_content_overview/"+page.meta.tutorial_id+".md" %}
</details>

#### Login to the Local MedPerf Server

The local MedPerf server is pre-configured with a dummy local authentication system. Remember that when you are communicating with the real MedPerf server, you should follow the steps in [this guide](../concepts/auth.md#login) to login. For the tutorials, it will be mocked. Since in this tutorial you will play multiple roles, you will login multiple times.

You are now ready to start!

## Training Setup with MedPerf (Model Owner, a.k.a. Experiment Admin)

```bash
medperf auth login -e testmo@example.com
```

### Define the data preparation Container

- Prepare the data preparation pipeline logic that will transform the raw clinical data into AI-ready data. This will be a container

### Register the Container

```bash
medperf container submit -n prep \
   -m "{{ prep_container }}"
```

### Define the training Containers

- Prepare the training logic using Nvidia Flare. There will be two containers: One to be used by the nodes (aggregator and clients), and one to be used by the experiment admin.

### Register the Training Node Container

```bash
medperf container submit -n trainer \
    -m "{{ train_container }}"
```

### Register the Training admin Container

```bash
medperf container submit -n trainadmin \
    -m "{{ admin_train_container }}"
```

### Register the Training Experiment

```bash
medperf training submit -n trainexp -d trainexp -p 2 -m 3 -a 4
```

The MedPerf server admin should approve the experiment.
Run:

```bash
bash admin_training_approval.sh
```

## Aggregator Setup with MedPerf (Aggregator Owner)

```bash
medperf auth login -e aggowner@example.com
```

### register aggregator

find hostname:

```bash
# This works for codespaces machine setup, for internal hostname.
# Other machine setup may need another command.
hostname -I | cut -d " " -f 1
```

Register two ports: 8102 and 8103

```bash
medperf aggregator submit -n aggreg -a <hostname_found> -p 8102 -p 8103
```

### Associate the aggregator with the experiment

```bash
medperf aggregator associate -a 1 -t 1
```

## Data preparation (Training Data Owner)

```bash
medperf auth login -e traincol1@example.com
```

### Process your data using the data prep container

```bash
medperf dataset create -p 1 -d datasets/col1 -l datasets/col1 --name col1 --description col1data --location col1location
```

### Register your dataset

find Hash:

```bash
medperf dataset ls
```

```bash
medperf dataset submit -d <hash_found>
```

### Request participation in the training experiment

```bash
medperf training associate_dataset -t 1 -d 1
```

## Redo the same with collaborator 2

```bash
bash collab_shortcut.sh
```

## Accepting Training Participation (Model Owner)

```bash
medperf auth login -e modelowner@example.com
```

### Accept participation requests

```bash
medperf training approve_association -t 1 -a 1
medperf training approve_association -t 1 -d 1
medperf training approve_association -t 1 -d 2
```

### Lock the experiment

```bash
medperf training lock -t 1
```

## Run the Aggregator (Aggregator Owner)

```bash
medperf auth login -e aggowner@example.com
```

```bash
medperf aggregator start -a 1 -t 1
```

(Now move to another terminal)

## Run Training (Training Data Owner)

First collaborator:

```bash
medperf auth login -e traincol1@example.com
```

```bash
medperf training run -d 1 -t 1
```

(Now move to another terminal)

Second collaborator:

```bash
medperf auth login -e traincol2@example.com
```

```bash
medperf training run -d 2 -t 1
