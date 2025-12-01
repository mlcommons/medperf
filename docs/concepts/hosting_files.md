# Hosting Files

MedPerf requires some assets to be hosted on the cloud when running machine learning pipelines. Submitting [Containers](../containers/containers.md) to the MedPerf server means submitting their metadata, **and not**, for example, model weights or code. [Container assets](container_assets.md) such as model weights or container image files need to be hosted on the cloud, and the submitted container metadata will only contain URLs (or certain identifiers) for these assets. Another example would be benchmark submission, where [demo datasets](../getting_started/benchmark_owner_demo.md#5-hosting-the-demo-dataset) need to be hosted.

The MedPerf client expects assets to be hosted in certain ways. Below are options of how assets can be hosted and how MedPerf identitfies them (e.g. a URL).

## File hosting

This can be done with any cloud hosting tool/provider you desire (such as GCP, AWS, Dropbox, Google Drive, Github). As long as your file can be accessed through a [direct download link](https://en.wikipedia.org/wiki/Direct_download_link), it will work with medperf. Generating a direct download link for your hosted file can be straight-forward when using some providers (e.g. Amazon Web Services, Google Cloud Platform, Microsoft Azure) and can be a bit tricky when using others (e.g. Dropbox, GitHub, Google Drive).

!!! Note
    Direct download links must be permanent

!!! tip
    You can make sure if a URL is a direct download link or not using tools like `wget` or `curl`. Running `wget <URL>` will download the file if the URL is a direct download link. Running `wget <URL>` may fail or may download an HTML page if the URL is not a direct download link.

When your file is hosted with a direct download link, MedPerf will be able to identify this file using that direct download link. So for example, when you are [submitting a model container](../getting_started/model_owner_demo.md#2-submitting-the-container), you should pass your hosted additional files URL as follows:

```bash
--additional-file <the-direct-download-link-to-the-additional-files-tarball>
```

!!! Warning
    Files in this case are supposed to have at least anonymous public read access permission.

## Synapse hosting

You can choose the option of hosting with [Synapse](https://www.synapse.org/) in cases where privacy is a concern. Please refer to [this link](https://help.synapse.org/docs/Uploading-and-Organizing-Data-Into-Projects,-Files,-and-Folders.2048327716.html) for hosting files on the Synapse platform.

When your file is hosted on Synapse, MedPerf will be able to identify this file using the Synapse ID corresponding to that file. So for example, when you are [submitting a model container](../getting_started/model_owner_demo.md#2-submitting-the-container), you would pass your hosted additional files URL as follows (note the prefix):

```bash
--additional-file synapse:<the-synapse-id-of-the-file>
```

Note that you need to authenticate with your Synapse credentials if you plan to use a Synaspe file with MedPerf. To do so run `medperf auth synapse_login`.

!!! note
    You **must** authenticate if using files on Synapse. If this is not necessary, this means the file has anonymous public access read permission. In this case, Synapse allows you to generate a permanent direct download link for your file and you can follow the [previous section](#file-hosting).

<!-- TODO: this should not be the case, it is better for the users if we fix this (easy to fix) -->
