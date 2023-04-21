# In Progress (Draft)

## File hosting
In order for Medperf users to retrieve and use files for their workflow, assests must be hosted separately and publicly. This can be done with any cloud hosting tool/provider you desire (such as GCP, AWS, Dropbox, Google Drive, Github). As long as your files can be accessed through an HTTP `GET` method, it should work with medperf. You can see if your files are hosted correctly by running
```
wget <asset_url>
```
If the file gets downloaded correctly just by using this command, then your hosting is compatible with Medperf.

## Github hosting
A great option for hosting small files is github, or equivalent repository hubs. It's important though to make sure the files won't be modified after being submitted to medperf, which could happen due to future commits. Because of this, the URLs of the files hosted on github must be UserContent github URLs (domain raw.githubusercontent.com) and contain a reference to the current commit hash. Below are the steps to get this URL for a specific file:

1. Open the github repository and ensure you are in the correct branch
2. Click on “Commits” at the right top corner of the repository explorer.
3. Locate the latest commit, it is the top most commit.
   1. If you are targeting previous versions of your file, make sure to consider the right commit.
4. Click on this button “&lt;>” corresponding to the commit (Browse the repository at this point in the history).
5. Navigate to the file of interest.
6. Click on “Raw”.
7. Copy the url from your browser.

Just as before, files hosted on github must be able to be retrieved through an HTTP `GET` call. 

## Synapse hosting
We provide the option of hosting with synapse, in cases where privacy is a concern. Synapse provides both asset storage and a container registry with well established data governance and sharing rules. Please refer to the following resources for file and docker submission to the Synapse platform:

- [Synapse: Uploading and Organizing Data Into Projects, Files and Folders](https://help.synapse.org/docs/Uploading-and-Organizing-Data-Into-Projects,-Files,-and-Folders.2048327716.html)
- [Synapse: Docker Registry](https://help.synapse.org/docs/Synapse-Docker-Registry.2011037752.html)

!!! note
    When using the Synapse Docker Registry to register MLCubes, make sure to also update the docker image name in your `mlcube.yaml` so it points to the Synapse Registry.

**Note:** 
