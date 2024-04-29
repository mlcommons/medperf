from medperf.entities.ca import CA
from medperf.entities.cube import Cube


def get_client_cert(ca: CA, email: str, output_path: str):
    """Responsible for getting a user cert"""
    common_name = email
    ca.prepare_config()
    params = {
        "ca_config": ca.config_path,
        "pki_assets": output_path,
    }
    env = {"MEDPERF_INPUT_CN": common_name}

    mlcube = Cube.get(ca.client_mlcube)
    mlube_task = "get_client_cert"
    mlcube.run(task=mlube_task, env_dict=env, **params)


def get_server_cert(ca: CA, address: str, output_path: str):
    """Responsible for getting a server cert"""
    common_name = address
    ca.prepare_config()
    params = {
        "ca_config": ca.config_path,
        "pki_assets": output_path,
    }
    env = {"MEDPERF_INPUT_CN": common_name}

    mlcube = Cube.get(ca.server_mlcube)
    mlube_task = "get_server_cert"
    mlcube.run(task=mlube_task, env_dict=env, port=80, **params)


def trust(ca: CA):
    """Verifies the CA cert fingerprint and writes it to the MedPerf storage.
    This is needed when running a workload, either by the users or
    by the aggregator
    """
    ca.prepare_config()
    params = {
        "ca_config": ca.config_path,
        "pki_assets": ca.pki_assets,
    }
    mlcube = Cube.get(ca.ca_mlcube)
    mlube_task = "trust"
    mlcube.run(task=mlube_task, **params)
