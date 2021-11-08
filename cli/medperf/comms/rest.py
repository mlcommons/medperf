import requests
import logging
import os

from medperf.utils import pretty_error, cube_path
from medperf.config import config
from medperf.comms import Comms
from medperf.enums import Role
from medperf.ui import UI


class REST(Comms):
    def __init__(self, ui: UI, server_url: str, token=None):
        self.server_url = server_url
        self.token = token
        self.ui = ui

    def login(self, username: str, password: str):
        """Authenticates the user with the server. Required for most endpoints

        Args:
            username (str): Username
            password (str): Password
        """
        body = {"username": username, "password": password}
        res = requests.post(f"{self.server_url}/auth-token/", json=body)
        if res.status_code != 200:
            logging.error(res.json())
            pretty_error("Unable to authenticate user with provided credentials")
        else:
            self.token = res.json()["token"]

    def authenticate(self):
        cred_path = config["credentials_path"]
        if os.path.exists(cred_path):
            with open(cred_path) as f:
                self.token = f.readline()
        else:
            pretty_error(
                "Couldn't find credentials file. Did you run 'medperf login' before?",
                self.ui,
            )

    def __auth_get(self, url, **kwargs):
        return self.__auth_req(url, requests.get, **kwargs)

    def __auth_post(self, url, **kwargs):
        return self.__auth_req(url, requests.post, **kwargs)

    def __auth_req(self, url, req_func, **kwargs):
        if self.token is None:
            pretty_error("Must be authenticated", self.ui)
        return req_func(url, headers={"Authorization": f"Token {self.token}"}, **kwargs)

    def benchmark_association(self, benchmark_uid: int) -> Role:
        """Retrieves the benchmark association

        Args:
            benchmark_uid (int): UID of the benchmark

        Returns:
            Role: the association type between current user and benchmark
        """
        res = self.__auth_get(f"{self.server_url}/me/benchmarks")
        if res.status_code != 200:
            logging.error(res.json())
            pretty_error(
                "there was an error retrieving the current user's benchmarks", self.ui
            )

        benchmarks = res.json()
        bm_dict = {bm["benchmark"]: bm for bm in benchmarks}
        rolename = None
        if benchmark_uid in bm_dict:
            rolename = bm_dict[benchmark_uid]["role"]
        return Role(rolename)

    def authorized_by_role(self, benchmark_uid: int, role: str) -> bool:
        """Indicates wether the current user is authorized to access
        a benchmark based on desired role 

        Args:
            benchmark_uid (int): UID of the benchmark
            role (str): Desired role to check for authorization

        Returns:
            bool: Wether the user has the specified role for that benchmark
        """
        assoc_role = self.benchmark_association(benchmark_uid)
        return assoc_role.name == role

    def get_benchmark(self, benchmark_uid: int) -> dict:
        """Retrieves the benchmark specification file from the server

        Args:
            benchmark_uid (int): uid for the desired benchmark

        Returns:
            dict: benchmark specification
        """
        res = self.__auth_get(f"{self.server_url}/benchmarks/{benchmark_uid}")
        if res.status_code != 200:
            logging.error(res.json())
            pretty_error("the specified benchmark doesn't exist", self.ui)
        benchmark = res.json()
        return benchmark

    def get_benchmark_models(self, benchmark_uid: int) -> list[int]:
        """Retrieves all the models associated with a benchmark. reference model not included

        Args:
            benchmark_uid (int): UID of the desired benchmark

        Returns:
            list[int]: List of model UIDS
        """
        res = self.__auth_get(f"{self.server_url}/benchmarks/{benchmark_uid}/models")
        if res.status_code != 200:
            logging.error(res.json())
            pretty_error(
                "couldn't retrieve models for the specified benchmark", self.ui
            )
        models = res.json()
        model_uids = [model["id"] for model in models]
        return model_uids

    def get_cube_metadata(self, cube_uid: int) -> dict:
        """Retrieves metadata about the specified cube

        Args:
            cube_uid (int): UID of the desired cube.

        Returns:
            dict: Dictionary containing url and hashes for the cube files
        """
        res = self.__auth_get(f"{self.server_url}/mlcubes/{cube_uid}/")
        if res.status_code != 200:
            logging.error(res.json())
            pretty_error("the specified cube doesn't exist", self.ui)
        metadata = res.json()
        return metadata

    def get_cube(self, url: str, cube_uid: int) -> str:
        """Downloads and writes an mlcube.yaml file from the server

        Args:
            url (str): URL where the mlcube.yaml file can be downloaded.
            cube_uid (int): Cube UID.

        Returns:
            str: location where the mlcube.yaml file is stored locally.
        """
        cube_file = config["cube_filename"]
        return self.__get_cube_file(url, cube_uid, "", cube_file)

    def get_cube_params(self, url: str, cube_uid: int) -> str:
        """Retrieves the cube parameters.yaml file from the server

        Args:
            url (str): URL where the parameters.yaml file can be downloaded.
            cube_uid (int): Cube UID.

        Returns:
            str: Location where the parameters.yaml file is stored locally.
        """
        ws = config["workspace_path"]
        params_file = config["params_filename"]
        return self.__get_cube_file(url, cube_uid, ws, params_file)

    def get_cube_additional(self, url: str, cube_uid: int) -> str:
        """Retrieves and stores the additional_files.tar.gz file from the server

        Args:
            url (str): URL where the additional_files.tar.gz file can be downloaded.
            cube_uid (int): Cube UID.

        Returns:
            str: Location where the additional_files.tar.gz file is stored locally.
        """
        add_path = config["additional_path"]
        tball_file = config["tarball_filename"]
        return self.__get_cube_file(url, cube_uid, add_path, tball_file)

    def __get_cube_file(self, url: str, cube_uid: int, path: str, filename: str):
        res = requests.get(url)
        if res.status_code != 200:
            logging.error(res.json())
            pretty_error(
                "There was a problem retrieving the specified file at " + url, self.ui
            )
        else:
            c_path = cube_path(cube_uid)
            path = os.path.join(c_path, path)
            if not os.path.isdir(path):
                os.makedirs(path)
            filepath = os.path.join(path, filename)
            open(filepath, "wb+").write(res.content)
            return filepath

    def upload_dataset(self, reg_dict: dict) -> int:
        """Uploads registration data to the server, under the sha name of the file.

        Args:
            reg_dict (dict): Dictionary containing registration information.

        Returns:
            int: id of the created dataset registration.
        """
        res = self.__auth_post(f"{self.server_url}/datasets/", json=reg_dict)
        if res.status_code != 201:
            logging.error(res.json())
            pretty_error("Could not upload the dataset", self.ui)
        return res.json()["id"]

    def upload_results(self, results_dict: dict) -> int:
        """Uploads results to the server.

        Args:
            results_dict (dict): Dictionary containing results information.

        Returns:
            int: id of the generated results entry
        """
        res = self.__auth_post(f"{self.server_url}/results/", json=results_dict)
        if res.status_code != 201:
            logging.error(res.json())
            pretty_error("Could not upload the results", self.ui)
        return res.json()["id"]

    def associate_dset_benchmark(self, data_uid: int, benchmark_uid: int):
        """Create a Dataset Benchmark association

        Args:
            data_uid (int): Registered dataset UID
            benchmark_uid (int): Benchmark UID
        """
        data = {"dataset": data_uid, "benchmark": benchmark_uid}
        res = self.__auth_post(f"{self.server_url}/datasets/benchmarks/", json=data)
        if res.status_code != 201:
            logging.error(res.json())
            pretty_error("Could not associate dataset to benchmark", self.ui)
