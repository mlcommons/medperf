# Copying your Dataset

When you register your dataset with MedPerf, your dataset will stay local on your machine. Suppose you decided to continue your work on a new machine; your local dataset needs to be copied/moved to the new machine and the MedPerf client installed on the new machine should be able to detect it.

This guide is for users who registered their dataset while working on a certain machine but they decide then to continue working on another machine. You can use MedPerf commands to easily copy your dataset to another machine.

## Step1: Export your dataset

First, you need to export your dataset into a `.gz` file so that the MedPerf client in the new machine later will be able to detect it and place it in the correct storage location.

Run the following command to export your dataset:

```bash
medperf dataset export --data_uid YOUR_DATASET_ID --output OUTPUT_FOLDER
```

Where:

- `YOUR_DATASET_ID` is your dataset ID,
- `OUTPUT_FOLDER` is a path to a folder where MedPerf will create the exported `.gz` file.

For example, the following command will export a dataset whose ID is `71`. The exported dataset file will be created inside the folder `./my_exported_dataset` and will be named `71.gz`.

```bash
medperf dataset export --data_uid 71 --output ./my_exported_dataset
```

## Step2: Import your dataset in the new Machine

On your new machine, make sure you have MedPerf setup and installed. Take the generated file from the previous step (i.e., the `.gz` file) and place it somewhere in your new machine.

Now to import the dataset into the MedPerf storage of the new machine, it depends on whether your dataset is still in development (i.e., you haven't fully prepared your dataset and haven't set it as operational), or if your dataset is operational.

### Case1: Your dataset is in Development

In this case, the exported dataset file contains your raw data, because you will need it in the new machine to continue preparing your dataset. Run the following command **in your new machine** to import your dataset:

```bash
medperf dataset import --data_uid YOUR_DATASET_ID --input PATH_TO_THE_GZ_FILE --raw_dataset_path PATH_TO_PLACE_YOUR_RAW_DATA
```

Where:

- `YOUR_DATASET_ID` is your dataset ID,
- `PATH_TO_THE_GZ_FILE` is the path to the `.gz` file you placed in the new machine,
- `PATH_TO_PLACE_YOUR_RAW_DATA` is the path to where the raw data will be placed in the new machine. This path should not already exist; MedPerf will create it.

### Case2: Your dataset is Operational

In this case, only your prepared data will be copied to the new machine. The raw data will remain on the old machine, as MedPerf no longer requires it. If you wish to move or back up your raw data for other purposes, you can do so using standard methods, such as manually transferring it. MedPerf on the new machine will not request or require access to it.

Run the following command **in your new machine** to import your dataset:

```bash
medperf dataset import --data_uid YOUR_DATASET_ID --input PATH_TO_THE_GZ_FILE
```

Where:

- `YOUR_DATASET_ID` is your dataset ID,
- `PATH_TO_THE_GZ_FILE` is the path to the `.gz` file you placed in the new machine,

## Considerations

When working on a new machine, keep in mind the following:

- Any MedPerf profile configurations you had on your old machine (e.g., container platform, gpus, ...) should be configured again in the new machine if you want them.
- It's advised to [logout](./auth.md#logout) on your old machine if you are not planning to use it anymore.
- Your dataset still exists on the old machine. You just created a copy of it in the new machine.
