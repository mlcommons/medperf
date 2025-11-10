from docker.errors import APIError
import pandas as pd
import requests
import yaml
from migration_cube import MigrationCube
import hashlib
import docker
import os
import synapseclient
from synapseclient.core.exceptions import SynapseNoCredentialsError
import json


UID_KEY = 'UID'
SYNAPSE_PREFIX = 'synapse:'


def get_container_info(req_session: requests.Session, synapse_client: synapseclient.Synapse,
                       download_link: str, container_id: str, expected_hash: str):
    is_synapse = download_link.startswith(SYNAPSE_PREFIX)

    if is_synapse:
        if synapse_client is None:
            print(f'Skipping Container {container_id}. It is a Synapse container.')
            container_info = None

        else:
            synapse_id = download_link.removeprefix(SYNAPSE_PREFIX)
            synapse_tmp_file = synapse_client.get(synapse_id)
            with open(synapse_tmp_file.path, 'r') as f:
                content = f.read()

            try:
                os.remove(synapse_tmp_file)
            except OSError:
                print(f'Failed to delete local Synapse file {synapse_tmp_file.path}. '
                      'Program will proceed without deleting it.')
    else:
        content = req_session.get(download_link).content

    content_hash = hashlib.sha256(content).hexdigest()
    hashes_matched = content_hash == expected_hash
    if not hashes_matched:
        print(f'Hash mismatch when downloading assets from Container ID {container_id}!\n'
              f'Asset Link: {download_link}\n'
              f'Expected hash: {expected_hash}, found hash: {content_hash}.\n'
              f'Continuing despite the mismatch...')
    container_info = yaml.safe_load(content)

    return container_info, hashes_matched


def get_docker_hash(docker_client: docker.client.DockerClient, container_dict: dict,
                    container_id: int, current_try: int = 1):
    MAX_TRIES = 5

    # MLCubes have a docker key, but the new container-config yaml simply has 'image' directly
    docker_info_dict = container_dict.get('docker', container_dict)
    try:
        image_info = docker_client.images.get_registry_data(docker_info_dict['image'])
        new_hash = image_info.id
        return new_hash
    except APIError:
        if current_try > MAX_TRIES:
            raise
        print(f'An error happened when attempting to get registry data from '
              f'Container {container_id}. Will try again {MAX_TRIES-current_try} times...')
        return get_docker_hash(docker_client=docker_client, container_dict=container_dict,
                               current_try=current_try + 1, container_id=container_id)


def get_container_hashes(input_json: os.PathLike, output_csv: os.PathLike, exclude_synapse: bool = False):

    request_session = requests.session()
    if not exclude_synapse:
        synapse_client = synapseclient.Synapse()

        try:
            print('Logging into Synapse with existing credentials (ie from medperf auth synapse login)')
            synapse_client.login(silent=True)
        except SynapseNoCredentialsError:
            msg = "There was an attempt to download resources from the Synapse "
            msg += "platform, but couldn't find Synapse credentials."
            msg += "\nDid you run 'medperf auth synapse_login' before?"
            raise ValueError(msg)
    else:
        synapse_client = None

    docker_client = docker.client.from_env()

    with open(input_json, 'r') as f:
        container_id_to_container = json.load(f)

    new_hashes_list = []
    for container_id, container_info in container_id_to_container.items():
        print(f'Analyzing Container {container_id}...')
        this_container_yaml, yaml_hash_matched = get_container_info(req_session=request_session,
                                                                    synapse_client=synapse_client,
                                                                    download_link=container_info['config_file'],
                                                                    container_id=container_id,
                                                                    expected_hash=container_info['mlcube_hash'])

        if this_container_yaml is not None:
            parameters_link = container_info.get('parameters_file')

            if parameters_link is not None:
                parameters_config, parameters_hash_matched = get_container_info(
                    req_session=request_session,
                    synapse_client=synapse_client,
                    download_link=parameters_link,
                    container_id=container_id,
                    expected_hash=container_info['parameters_hash']
                )
            else:
                parameters_config = {}

            new_hash = get_docker_hash(docker_client=docker_client, container_dict=this_container_yaml,
                                       container_id=container_id)
            id_value = container_info['old_image_hash']
            if not id_value.startswith('sha256:'):
                id_value = f'sha256:{id_value}'

            if 'id' in container_info['old_metadata'].keys():
                # Already updated, do not change
                new_metadata = container_info['old_metadata']
            else:
                # Old format, update
                new_metadata = {'id': id_value}
        else:
            new_hash = new_metadata = parameters_config = parameters_hash_matched = None

        update_dict = {
            'uid': container_id,
            'old_hash': container_info['old_image_hash'],
            'new_hash': new_hash,
            'new_metadata': new_metadata,
            'container_config': this_container_yaml,
            'container_config_hashes_matched': yaml_hash_matched,
            'parameters_config': parameters_config,
            'parameters_hash_matched': parameters_hash_matched
        }
        new_hashes_list.append(update_dict)

    new_hashes_df = pd.DataFrame(new_hashes_list)
    new_hashes_df.to_json(output_csv, index=False, indent=4)


def get_container_jsons(output_file: os.PathLike,include_public_links: bool = True,
                        include_synapse_links: bool = False):
    containers = MigrationCube.all()
    containers: list[MigrationCube] = sorted(containers, key=lambda x: x.id)

    all_containers = {}
    for container in containers:

        config_file_url = container.git_mlcube_url
        is_synapse = config_file_url.startswith(SYNAPSE_PREFIX)

        if (is_synapse and not include_synapse_links) or (not is_synapse and not include_public_links):
            continue

        container_info = {
            'uid': container.id,
            'name': container.name,
            'config_file': container.git_mlcube_url,
            'mlcube_hash': container.mlcube_hash,
            'parameters_file': container.git_parameters_url,
            'parameters_hash': container.parameters_hash,
            'old_image_hash': container.image_hash,
            'old_metadata': container.metadata
        }
        all_containers[container.id] = container_info

    with open(output_file, 'w') as f:
        json.dump(all_containers, f, indent=4)
