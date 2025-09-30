from docker.errors import APIError
import pandas as pd
import requests
import yaml
from medperf.entities.cube import Cube
import docker
import os
import synapseclient
from synapseclient.core.exceptions import SynapseNoCredentialsError
from enum import Enum, auto
import json

UID_KEY = 'UID'

class Platforms(Enum):
    synapse = auto()
    public = auto()


def get_container_info(req_session: requests.Session, container: Cube, synapse_client: synapseclient.Synapse):
    synapse_prefix = 'synapse:'
    if container.git_mlcube_url.startswith(synapse_prefix):
        platform = Platforms.synapse
        if synapse_client is None:
            print(f'Skipping Container {container.id}. It is a Synapse container.')
            container_info = None

        else:
            synapse_id = container.git_mlcube_url.removeprefix(synapse_prefix)
            synapse_tmp_file = synapse_client.get(synapse_id)
            with open(synapse_tmp_file.path, 'r') as f:
                container_info = yaml.safe_load(f.read())
            try:
                os.remove(synapse_tmp_file)
            except OSError:
                print(f'Failed to delete local Synapse file {synapse_tmp_file.path}. '
                      'Program will proceed without deleting it.')
    else:
        platform = Platforms.public
        if req_session is None:
            container_info = None
            print(f'Skipping Container {container.id}. It is a Public container.')
        with req_session.get(container.git_mlcube_url) as response:
            container_info = yaml.safe_load(response.content)

    return container_info, platform


def get_docker_hash(docker_client: docker.client.DockerClient, container_dict: dict,
                          container_id: int, current_try: int = 1):
    MAX_TRIES = 5

    #MLCubes have a docker key, but the new container-config yaml simply has 'image' directly
    docker_info_dict = container_dict.get('docker', container_dict)
    try:
        image_info = docker_client.images.get_registry_data(docker_info_dict['image'])
        new_hash = image_info.id
        return new_hash
    except APIError:
        if current_try > MAX_TRIES:
            raise
        print(f'An error happened when attempting to get registry data from Container {container_id}. Will try again {MAX_TRIES-current_try} times...')
        return get_docker_hash(docker_client=docker_client, container_dict=container_dict,
                                     current_try=current_try+1, container_id=container_id)


def get_container_yamls(output_public_path: os.PathLike, output_synapse_path: os.PathLike, 
                        include_public_links: bool = True, include_synapse_links: bool = False):
    if include_public_links:
        request_session = requests.session()
    else: 
        request_session = None

    if include_synapse_links:
        synapse_client = synapseclient.Synapse()

        try:
            synapse_client.login(silent=True)
        except SynapseNoCredentialsError:
            msg = "There was an attempt to download resources from the Synapse "
            msg += "platform, but couldn't find Synapse credentials."
            msg += "\nDid you run 'medperf auth synapse_login' before?"
            raise ValueError(msg)
    else:
        synapse_client = None

    print(f'Getting basic information on all containers in the MedPerf server...')
    containers =  Cube.all()
    containers: list[Cube] = sorted(containers, key=lambda x: x.id)
    
    docker_client = docker.client.from_env()

    new_hashes_dict = {
        Platforms.public: [],
        Platforms.synapse: []
    }

    for container in containers:
        print(f'Analyzing Container {container.id}...')
        this_container_yaml, platform = get_container_info(req_session=request_session, synapse_client=synapse_client, container=container)

        if this_container_yaml is not None:
            new_hash = get_docker_hash(docker_client=docker_client, container_dict=this_container_yaml,
                                                container_id=container.id)
            id_value = container.image_hash
            if not id_value.startswith('sha256:'):
                id_value = f'sha256:{id_value}'

            if 'id' in container.metadata.keys():
                # Already updated, do not change
                new_metadata = container.metadata
            else:
                # Old format, update
                new_metadata = {'id': id_value}
        else:
            new_hash = new_metadata = None

        update_dict = {
            'uid': container.id,
            'old_hash': container.image_hash,
            'new_hash': new_hash,
            'new_metadata': json.dumps(new_metadata)
        }
        new_hashes_dict[platform].append(update_dict)

    if include_public_links:
        print(f'Saving new hashes for Public Containers to file {output_public_path}...')
        public_df = pd.DataFrame(new_hashes_dict[Platforms.public])
        public_df.to_csv(output_public_path, index=False)

    if include_synapse_links:
        print(f'Saving new hashes for Synapse Containers to file {output_synapse_path}...')
        synapse_df = pd.DataFrame(new_hashes_dict[Platforms.synapse])
        synapse_df.to_csv(output_synapse_path, index=False)