# Medperf Data Preparation Dashboard

The medperf data preparation dashboard provides visualization on the usage of a data preparation mlcube and the stages data owners are at. This will hopefully provide insights into how far along the process is going, and wether users are having trouble specific to the execution of the data preparation pipeline.

## Installation

To install, execute the following command at this folder:

```
pip install -e .
```

## How to use

To use, you need to have a few assets and identifiers beforehand:
- MLCube ID: The ID of the MLCube that is being used as a data preparation MLCube. To be able to see progress, you must be the owner of this MLCube
- Stages File: A `CSV` file that contains the human-readable information of each of the stages that the data preparation MLCube contains. The CSV should have the following columns: `Status Code, status_name, comment, docs_url, color`
- Institutions File: A `CSV` file that maps emails to institutions that are expected to be part of the preparation procedure. The CSV should have the following columns: `institution, email`

Once all requirements are covered, you can execute the following command:

```
medperf-dashboard -m <MLCube ID> -s <Stages File> -i <Institutions File>
```

Running this command will fetch the latest reports from the medperf server, and start a local server that will contain the visualization of the progress. To access this server, head to `http://localhost:8050` on your preferred browser.