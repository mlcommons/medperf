# Submitting an Encrypted Model

## About the Guide

You will learn how to register an **encrypted model container** to MedPerf and participate in a benchmark. Additionally, you will learn how to:

- Grant temporary access to authorized Data Owners
- Revoke access after the benchmark is complete

The following outlines the steps involved:

1. Create your model container (no MedPerf)
2. Export and encrypt your model container
3. Host the encrypted file publicly
4. Login and register your encrypted model
5. Associate your model with a benchmark
6. Manage access
7. Revoke access after benchmark completion

## 1. Create Your Model Container

Before using MedPerf, you need to create a Docker container that packages your model. This step happens entirely outside of MedPerf.

### Understanding Container Requirements

Your container must be compatible with the benchmark workflow:

- Accept input data in the format specified by the benchmark's data preparation container
- Output predictions in the format expected by the benchmark's metrics container
- Include all necessary dependencies and runtime requirements

Learn more about [containers in MedPerf here](../containers/containers.md). Use [this file](https://github.com/mlcommons/medperf/blob/main/examples/chestxray_tutorial/model_custom_cnn_encrypted/container_config.yaml) as a template for your `container_config.yaml` file.

## 2. Export and Encrypt Your Model Container

We [provide a script](https://github.com/mlcommons/medperf/tree/main/scripts/encrypt_container) that you can use to:

- Export your docker image into a docker archive,
- Then, encrypt the docker archive using GPG.

After encryption, you will end up with the encrypted archive file, and the decryption key.

## 3. Host the Encrypted File

You need to upload your encrypted archive to a publicly accessible location (e.g., on a cloud bucket) so that it can be accessed using a direct download link.

After that, make sure your `container_config.yaml` file that you created in step 1 references the URL of the hosted encrypted archive (in the `image` field of the config file).

## 4. Register Your Encrypted Model

Now you are ready to register your encrypted model to the MedPerf server. Open the web UI, Make sure you are logged in to MedPerf, and:

- Navigate to the `Models` tab
- Click on `Register a New Container Model`
- Fill in the form. Make sure choose the encrypted model option, and insert the path of the decryption key.

Note that the decryption key will not be uploaded to the MedPerf server. Referencing the key during the model registration is only for the MedPerf client to copy the key to MedPerf-managed folder in your home directory, so that in later steps, the MedPerf client knows where the decryption key resides. The decryption key will be used by the MedPerf client only in the following scenarios:

- When associating with a benchmark: a local compatibility test of your model with the benchmark will be executed. So, the MedPerf client will decrypt your model (locally on your machine) when running the test. This is to make sure that both decrypting your model and running it on a toy dataset work fine.
- When granting access to authorized data owners: the MedPerf client will read the decryption key, encrypt it to be accessible only to the authorized data owners, and upload the encrypted version of your decryption key to the MedPerf server (to transport it to the authorized data owners).

## 5. Associate Your Model with a Benchmark

Now that your encrypted model is registered, you can request to participate in a benchmark.

### Navigate to Your Model Page

From the `Models` tab, click on your encrypted model to view its detail page.

### Start Association Request

Click the **"Associate with a benchmark"** button. Select the benchmark and proceed. This will run a compatibility test with the benchmark test dataset locally on your machine. You will be prompted at the end of the test to approve sending the test results to the MedPerf server.

## 6. Manage Access

Once your association request is approved by the Benchmark Committee, you need to give access to the authorized data owners.

### Navigate to Access Management

On your model's detail page, click on the **"Manage Access"** button.

Under the `Grant Access` section, you should fill the following information:

- The benchmark ID to which the data owners should be associated.
- The list of emails of the data owners you wish to provide access to.

Then click the `grant access` button.

### Auto-give access

Recall that giving access to a data owner means that the MedPerf client will encypt your decryption key using the data owner's public key (i.e., certificate). It may not be practical to wait for each data owner to create their certificates before you grant access, and also, you may not want to make data owners wait until you click grant access.

For this reason, you can use the automatic grant access feature, where the MedPerf client will automatically check for new authorized data owners who obtained their certificates, and grant them access. You can specify the frequency of checks.

## 7. Monitoring and Revoking Access

At any time you can check the `Current Access` section to see who currently have access. You may also want to revoke access to a certain participant if, for example, you knew their private key was leaked.

Also, after all data owners successfully run your model, it's recommended that you click the `delete keys` button to revoke access to all data owners.
