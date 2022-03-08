from typing import List
import requests
import logging
import os

from medperf.ui.interface import UI
from medperf.enums import Role
import medperf.config as config
from medperf.comms.interface import Comms
from medperf.utils import pretty_error, cube_path, storage_path, generate_tmp_uid


class REST(Comms):
    def __init__(self, source: str, ui: UI, token=None):
        self.server_url = source
        self.token = token
        self.ui = ui

    def login(self, ui: UI):
        """Authenticates the user with the server. Required for most endpoints

        Args:
            ui (UI): Instance of an implementation of the UI interface
        """
        user = ui.prompt("username: ")
        pwd = ui.hidden_prompt("password: ")
        body = {"username": user, "password": pwd}
        res = requests.post(f"{self.server_url}/auth-token/", json=body)
        if res.status_code != 200:
            pretty_error("Unable to authenticate user with provided credentials", ui)
        else:
            self.token = res.json()["token"]

    def authenticate(self):
        cred_path = storage_path(config.credentials_path)
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

    def get_benchmarks(self) -> List[dict]:
        """Retrieves all benchmarks in the platform.

        Returns:
            List[dict]: all benchmarks information.
        """
        res = self.__auth_get(f"{self.server_url}/benchmarks/")
        if res.status_code != 200:
            logging.error(res.json())
            pretty_error("couldn't retrieve benchmarks", self.ui)
        benchmarks = res.json()
        return benchmarks

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

    def get_benchmark_models(self, benchmark_uid: int) -> List[int]:
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

    def get_benchmark_demo_dataset(
        self, demo_data_url: str, uid: str = generate_tmp_uid()
    ) -> str:
        """Downloads the benchmark demo dataset and stores it in the user's machine

        Args:
            demo_data_url (str): location of demo data for download
            uid (str): UID to use for storing the demo dataset. Defaults to generate_tmp_uid().

        Returns:
            str: path where the downloaded demo dataset can be found
        """
        tmp_dir = storage_path(config.tmp_storage)
        demo_data_path = os.path.join(tmp_dir, uid)
        tball_file = config.tarball_filename
        filepath = os.path.join(demo_data_path, tball_file)

        # Don't re-download if something already exists with same uid
        if os.path.exists(filepath):
            return filepath

        res = requests.get(demo_data_url)
        if res.status_code != 200:
            logging.error(res.json())
            pretty_error("couldn't download the demo dataset", self.ui)

        os.mkdir(demo_data_path)

        open(filepath, "wb+").write(res.content)
        return filepath

    def get_user_benchmarks(self) -> List[dict]:
        """Retrieves all benchmarks created by the user

        Returns:
            List[dict]: Benchmarks data
        """
        res = self.__auth_get(f"{self.server_url}/me/benchmarks/")
        if res.status_code != 200:
            logging.error(res.json())
            pretty_error("wasn't able to retrieve user benchmarks", self.ui)

    def get_cubes(self) -> List[dict]:
        """Retrieves all MLCubes in the platform

        Returns:
            List[dict]: List containing the data of all MLCubes
        """
        res = self.__auth_get(f"{self.server_url}/mlcubes/")
        if res.status_code != 200:
            logging.error(res.json())
            pretty_error("couldn't retrieve mlcubes from the platform")
        return res.json()

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
        cube_file = config.cube_filename
        return self.__get_cube_file(url, cube_uid, "", cube_file)

    def get_user_cubes(self) -> List[dict]:
        """Retrieves metadata from all cubes registered by the user

        Returns:
            List[dict]: List of dictionaries containing the mlcubes registration information
        """
        res = self.__auth_get(f"{self.server_url}/me/mlcubes/")
        if res.status_code != 200:
            logging.error(res.json())
            pretty_error("couldn't retrieve mlcubes created by the user")
        data = res.json()
        return data

    def get_cube_params(self, url: str, cube_uid: int) -> str:
        """Retrieves the cube parameters.yaml file from the server

        Args:
            url (str): URL where the parameters.yaml file can be downloaded.
            cube_uid (int): Cube UID.

        Returns:
            str: Location where the parameters.yaml file is stored locally.
        """
        ws = config.workspace_path
        params_file = config.params_filename
        return self.__get_cube_file(url, cube_uid, ws, params_file)

    def get_cube_additional(self, url: str, cube_uid: int) -> str:
        """Retrieves and stores the additional_files.tar.gz file from the server

        Args:
            url (str): URL where the additional_files.tar.gz file can be downloaded.
            cube_uid (int): Cube UID.

        Returns:
            str: Location where the additional_files.tar.gz file is stored locally.
        """
        add_path = config.additional_path
        tball_file = config.tarball_filename
        return self.__get_cube_file(url, cube_uid, add_path, tball_file)

    def __get_cube_file(self, url: str, cube_uid: int, path: str, filename: str):
        res = requests.get(url)
        if res.status_code != 200:
            logging.error(f"Retrieving cube file failed with: {res.status_code}")
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

    def upload_benchmark(self, benchmark_dict: dict) -> int:
        """Uploads a new benchmark to the server.

        Args:
            benchmark_dict (dict): benchmark_data to be uploaded

        Returns:
            int: UID of newly created benchmark
        """
        res = self.__auth_post(f"{self.server_url}/benchmarks/", json=benchmark_dict)
        if res.status_code != 201:
            logging.error(res.json())
            pretty_error("Could not upload benchmark", self.ui)

    def upload_mlcube(self, mlcube_body: dict) -> int:
        """Uploads an MLCube instance to the platform

        Args:
            mlcube_body (dict): Dictionary containing all the relevant data for creating mlcubes

        Returns:
            int: id of the created mlcube instance on the platform
        """
        res = self.__auth_post(f"{self.server_url}/mlcubes/", json=mlcube_body)
        if res.status_code != 201:
            logging.error(res.json())
            pretty_error("Could not upload the mlcube", self.ui)
        return res.json()["id"]

    def get_datasets(self) -> List[dict]:
        """Retrieves all datasets in the platform

        Returns:
            List[dict]: List of data from all datasets
        """
        res = self.__auth_get(f"{self.server_url}/datasets/")
        if res.status_code != 200:
            logging.error(res.json())
            pretty_error("could not retrieve datasets from server", self.ui)
        return res.json()

    def get_user_datasets(self) -> dict:
        """Retrieves all datasets registered by the user

        Returns:
            dict: dictionary with the contents of each dataset registration query
        """
        res = self.__auth_get(f"{self.server_url}/me/datasets/")
        if res.status_code != 200:
            logging.error(res.json())
            pretty_error("Could not retrieve datasets from server", self.ui)
        return res.json()

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

    def get_user_results(self) -> dict:
        """Retrieves all results registered by the user

        Returns:
            dict: dictionary with the contents of each dataset registration query
        """
        res = self.__auth_get(f"{self.server_url}/me/results/")
        if res.status_code != 200:
            logging.error(res.json())
            pretty_error("Could not retrieve results from server", self.ui)
        return res.json()

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

    def associate_dset(self, data_uid: int, benchmark_uid: int):
        """Create a Dataset Benchmark association

        Args:
            data_uid (int): Registered dataset UID
            benchmark_uid (int): Benchmark UID
        """
        data = {
            "dataset": data_uid,
            "benchmark": benchmark_uid,
            "approval_status": "PENDING",
        }
        res = self.__auth_post(f"{self.server_url}/datasets/benchmarks/", json=data)
        if res.status_code != 201:
            logging.error(res.json())
            pretty_error("Could not associate dataset to benchmark", self.ui)

    def associate_cube(self, cube_uid: str, benchmark_uid: int):
        """Create an MLCube-Benchmark association

        Args:
            cube_uid (str): MLCube UID
            benchmark_uid (int): Benchmark UID
        """
        data = {
            "results": {},
            "approval_status": "PENDING",
            "model_mlcube": cube_uid,
            "benchmark": benchmark_uid,
        }
        res = self.__auth_post(f"{self.server_url}/mlcubes/benchmarks/", json=data)
        if res.status_code != 201:
            logging.error(res.json())
            pretty_error("Could not associate dataset to benchmark", self.ui)
