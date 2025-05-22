# Hosting Files

MedPerf requires some assets to be hosted on the cloud when running machine learning pipelines. Submitting [Containers](../containers/containers.md) to the MedPerf server means submitting their metadata, **and not**, for example, model weights or parameters files. [Container assets](container_assets.md) such as model weights need to be hosted on the cloud, and the submitted container metadata will only contain URLs (or certain identifiers) for these assets. Another example would be benchmark submission, where [demo datasets](../getting_started/benchmark_owner_demo.md#5-hosting-the-demo-dataset) need to be hosted.

The MedPerf client expects assets to be hosted in certain ways. Below are options of how assets can be hosted and how MedPerf identitfies them (e.g. a URL).

## File hosting

This can be done with any cloud hosting tool/provider you desire (such as GCP, AWS, Dropbox, Google Drive, Github). As long as your file can be accessed through a [direct download link](https://en.wikipedia.org/wiki/Direct_download_link), it will work with medperf. Generating a direct download link for your hosted file can be straight-forward when using some providers (e.g. Amazon Web Services, Google Cloud Platform, Microsoft Azure) and can be a bit tricky when using others (e.g. Dropbox, GitHub, Google Drive).

!!! Note
    Direct download links must be permanent

!!! tip
    You can make sure if a URL is a direct download link or not using tools like `wget` or `curl`. Running `wget <URL>` will download the file if the URL is a direct download link. Running `wget <URL>` may fail or may download an HTML page if the URL is not a direct download link.

When your file is hosted with a direct download link, MedPerf will be able to identify this file using that direct download link. So for example, when you are [submitting a container](../getting_started/model_owner_demo.md#2-submitting-the-container), you should pass your hosted container config file as follows:

```bash
--container-config <the-direct-download-link-to-the-file>
```

!!! Warning
    Files in this case are supposed to have at least anonymous public read access permission.

### Direct download links of files on GitHub

It was a common practice by the current MedPerf users to host files on GitHub. You can learn below how to find the direct download link of a file hosted on GitHub. You can check online for other storage providers.

It's important though to make sure the files won't be modified after their URLs are submitted to medperf, which could happen due to future commits. Because of this, the URLs of the files hosted on GitHub must contain a reference to the corresponding commit hash. Below are the steps to get this URL for a specific file:

1. Open the GitHub repository and ensure you are in the correct branch
2. Click on “Commits” at the right top corner of the repository explorer.
3. Locate the latest commit, it is the top most commit.
   1. If you are targeting previous versions of your file, make sure to consider the right commit.
4. Click on this button “&lt;>” corresponding to the commit (Browse the repository at this point in the history).
5. Navigate to the file of interest.
6. Click on “Raw”.
7. Copy the url from your browser. It should be a UserContent GitHub URLs (domain raw.githubusercontent.com).

## Synapse hosting

You can choose the option of hosting with [Synapse](https://www.synapse.org/) in cases where privacy is a concern. Please refer to [this link](https://help.synapse.org/docs/Uploading-and-Organizing-Data-Into-Projects,-Files,-and-Folders.2048327716.html) for hosting files on the Synapse platform.

When your file is hosted on Synapse, MedPerf will be able to identify this file using the Synapse ID corresponding to that file. So for example, when you are [submitting a container](../getting_started/model_owner_demo.md#2-submitting-the-container), you would pass your hosted container config file as follows (note the prefix):

```bash
--container-config synapse:<the-synapse-id-of-the-file>
```

Note that you need to authenticate with your Synapse credentials if you plan to use a Synaspe file with MedPerf. To do so run `medperf auth synapse_login`.

!!! note
    You **must** authenticate if using files on Synapse. If this is not necessary, this means the file has anonymous public access read permission. In this case, Synapse allows you to generate a permanent direct download link for your file and you can follow the [previous section](#file-hosting).

<!-- TODO: this should not be the case, it is better for the users if we fix this (easy to fix) -->
