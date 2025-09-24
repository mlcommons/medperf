from medperf.entities.cube import Cube
from medperf.init import initialize
import aiohttp
import asyncio
import yaml
import time
import docker
import pandas as pd
from docker.errors import APIError

initialize()
UID_KEY = 'UID'

async def get_container_info(session: aiohttp.ClientSession, container: Cube):

    container_config_url = container.git_mlcube_url
    container_uid = container.id
    
    if container_config_url.startswith('synapse'):
        container_info = {}
    else:
        async with session.get(container_config_url) as response:
            actual_response = await response.text()
            container_info = yaml.safe_load(actual_response)
    container_info[UID_KEY] = container_uid
    return container_info

async def get_all_container_infos(container_list: list[dict]):
    async with aiohttp.ClientSession() as session:
        tasks = [get_container_info(session=session, container=container)
                               for container in container_list]
        container_info_list  = await asyncio.gather(*tasks)
    
    return container_info_list

def get_docker_image_info(docker_client: docker.client.DockerClient, container_dict: dict,
                          container_id: int, current_try: int = 1):
    MAX_TRIES = 5
    try:
        image_info = docker_client.images.get_registry_data(container_dict['docker']['image'])
        new_hash = image_info.id
        return new_hash
    except APIError:
        if current_try > MAX_TRIES:
            raise
        print(f'An error happened when attempting to get registry data from Container {container_id}. Will try again {MAX_TRIES-current_try} times...')
        return get_docker_image_info(docker_client=docker_client, container_dict=container_dict,
                                     current_try=current_try+1, container_id=container_id)


async def get_container_yamls():

    containers =  Cube.all()
    containers = sorted(containers, key=lambda x: x.id)
    yaml_dict_list = await get_all_container_infos(container_list=containers)  # TODO run all after testing
    id_to_yaml = {yaml_content[UID_KEY]: yaml_content for yaml_content in yaml_dict_list}
    docker_client = docker.client.from_env()

    update_dict_list = []
    for container in containers:
        print(f'Analyzing Container {container.id}...')
        this_container_yaml = id_to_yaml[container.id]

        if 'docker' in this_container_yaml:
            new_hash = get_docker_image_info(docker_client=docker_client, container_dict=this_container_yaml,
                                             container_id=container.id)
            new_metadata = {'id': container.image_hash}
        else:
            new_hash = new_metadata = None

        update_dict = {
            'uid': container.id,
            'old_hash': container.image_hash,
            'new_hash': new_hash,
            'new_metadata': new_metadata
        }
        update_dict_list.append(update_dict)

    update_df = pd.DataFrame(update_dict_list)
    update_df.to_csv('update_containers.csv') 
    return yaml_dict_list

def generate_updated_ids():
    container_yaml_files = asyncio.run(get_container_yamls())
    return container_yaml_files
if __name__ == '__main__':
    start = time.perf_counter()
    res = generate_updated_ids()
    end = time.perf_counter()
