from typing import List
import requests
import logging
import os

from medperf.utils import pretty_error, cube_path, storage_path
import medperf.config as config
from medperf.comms import Comms
from medperf.enums import Role
from medperf.ui import UI


class REST(Comms):
    def __init__(self, source: str, ui: UI, token=None):
        self.server_url = self.__parse_url(source)
        self.token = token
        self.ui = ui
        self.cert = config.certificate
        if self.cert is None:
            # No certificate provided, default to normal verification
            self.cert = True

    def __parse_url(self, url):
        url_sections = url.split("://")
        # Remove protocol if passed
        if len(url_sections) > 1:
            url = "".join(url_sections[1:])

        return f"https://{url}"

    def login(self, ui: UI):
        """Authenticates the user with the server. Required for most endpoints

        Args:
            ui (UI): Instance of an implementation of the UI interface
        """
        user = ui.prompt("username: ")
        pwd = ui.hidden_prompt("password: ")
        body = {"username": user, "password": pwd}
        res = self.__req(f"{self.server_url}/auth-token/", requests.post, json=body)
        if res.status_code != 200:
            pretty_error("Unable to authenticate user with provided credentials", ui)
        else:
            self.token = res.json()["token"]

    def change_password(self, pwd: str) -> bool:
        """Sets a new password for the current user.

        Args:
            pwd (str): New password to be set
            ui (UI): Instance of an implementation
        Returns:
            bool: Whether changing the password was successful or not
        """
        body = {"password": pwd}
        res = self.__auth_post(f"{self.server_url}/me/password/", json=body)
        if res.status_code != 200:
            pretty_error("Unable to change the current password", self.ui)
            return False
        return True

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

    def __auth_put(self, url, **kwargs):
        return self.__auth_req(url, requests.put, **kwargs)

    def __auth_req(self, url, req_func, **kwargs):
        if self.token is None:
            pretty_error("Must be authenticated", self.ui)
        return self.__req(
            url, req_func, headers={"Authorization": f"Token {self.token}"}, **kwargs
        )

    def __req(self, url, req_func, **kwargs):
        try:
            return req_func(url, verify=self.cert, **kwargs)
        except requests.exceptions.SSLError as e:
            logging.error(f"Couldn't connect to {self.server_url}: {e}")
            pretty_error(
                "Couldn't connect to server through HTTPS. If running locally, "
                "remember to provide the server certificate through --certificate",
                self.ui,
            )

    def __set_approval_status(self, url: str, status: str) -> requests.Response:
        """Sets the approval status of a resource

        Args:
            url (str): URL to the resource to update
            status (str): approval status to set

        Returns:
            requests.Response: Response object returned by the update
        """
        data = {"approval_status": status}
        res = self.__auth_put(url, json=data,)
        return res

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

    def get_cube_image(self, url: str, cube_uid: int) -> str:
        """Retrieves and stores the image file from the server

        Args:
            url (str): URL where the image file can be downloaded.
            cube_uid (int): Cube UID.

        Returns:
            str: Location where the image file is stored locally.
        """
        image_path = config.image_path
        image_name = url.split("/")[-1]
        return self.__get_cube_file(url, cube_uid, image_path, image_name)

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

    def associate_dset_benchmark(self, data_uid: int, benchmark_uid: int):
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

    def set_dataset_association_approval(
        self, dataset_uid: str, benchmark_uid: str, status: str
    ):
        """Approves a dataset association

        Args:
            dataset_uid (str): Dataset UID
            benchmark_uid (str): Benchmark UID
            status (str): Approval status to set for the association
        """
        url = f"{self.server_url}/datasets/{dataset_uid}/benchmarks/{benchmark_uid}/"
        res = self.__set_approval_status(url, status)
        if res.status_code != 200:
            logging.error(res.json())
            pretty_error(
                f"Could not approve association between dataset {dataset_uid} and benchmark {benchmark_uid}",
                self.ui,
            )

    def set_mlcube_association_approval(
        self, mlcube_uid: str, benchmark_uid: str, status: str
    ):
        """Approves an mlcube association

        Args:
            mlcube_uid (str): Dataset UID
            benchmark_uid (str): Benchmark UID
            status (str): Approval status to set for the association
        """
        url = f"{self.server_url}/mlcubes/{mlcube_uid}/benchmarks/{benchmark_uid}/"
        res = self.__set_approval_status(url, status)
        if res.status_code != 200:
            logging.error(res.json())
            pretty_error(
                f"Could not approve association between mlcube {mlcube_uid} and benchmark {benchmark_uid}",
                self.ui,
            )

    def get_datasets_associations(self) -> List[dict]:
        """Get all dataset associations related to the current user

        Returns:
            List[dict]: List containing all associations information
        """
        res = self.__auth_get(f"{self.server_url}/me/datasets/associations/")
        if res.status_code != 200:
            logging.error(res.json())
            pretty_error("Could not retrieve user datasets associations", self.ui)
        return res.json()

    def get_cubes_associations(self) -> List[dict]:
        """Get all cube associations related to the current user

        Returns:
            List[dict]: List containing all associations information
        """
        res = self.__auth_get(f"{self.server_url}/me/mlcubes/associations/")
        if res.status_code != 200:
            logging.error(res.json())
            pretty_error("Could not retrieve user mlcubes associations", self.ui)
        return res.json()
