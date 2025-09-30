The scripts in this directory can be used to download the Container information from the MedPerf server and generate CSV files for updating the old format hashes to new format hashes (equivalent to the image digest on DockerHub).

Usage:
1- Run `get_container_info_from_medperf.py` to download container information form the MedPerf server and save locally as a `.json` file. The `-p` flag must be set to download information from publically available containers, while the `-s` flag must be set to download inbformation from containers available in the Synapse platform. **At least one of the `-p` and/or `-s` flags must be supplied!** The `-o` flag may be optionally supplied to provide a destination file path. Example command:
```shell
python get_container_info_from_medperf.py -p -o example.json
```

2- Run `generate_updated_hashes.py` to generate a `.csv` file containing the new container hashes. The `-i` argument must be supplied with the output json file from step 1. The `-o` argument may optionally be supplied to provide a specific destination path for the generated `.csv` file. Finally, the `-s` file may be supplied to instantiate a `synapseclient` to download Synapse containers, if necessary and/or desired. This function assumes a local Synapse login was done previously using a PAT (for example, via the `medperf auth synapse_login` command)

3- The generated csv file should contain the container IDs, their old hashes, new hashes and new metadata.
