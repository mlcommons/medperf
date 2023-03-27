from typing import List
import requests
import logging

from medperf.enums import Status
import medperf.config as config
from medperf.comms.interface import Comms
from medperf.utils import (
    read_credentials,
    sanitize_json,
    log_response_error,
)
from medperf.exceptions import (
    CommunicationError,
    CommunicationRetrievalError,
    CommunicationAuthenticationError,
    CommunicationRequestError,
)


class REST(Comms):
    def __init__(self, source: str, token=None):
        self.server_url = self.parse_url(source)
        self.token = token
        self.cert = config.certificate
        if self.cert is None:
            # No certificate provided, default to normal verification
            self.cert = True

    @classmethod
    def parse_url(cls, url: str) -> str:
        """Parse the source URL so that it can be used by the comms implementation.
        It should handle protocols and versioning to be able to communicate with the API.

        Args:
            url (str): base URL

        Returns:
            str: parsed URL with protocol and version
        """
        url_sections = url.split("://")
        api_path = f"/api/v{config.major_version}"
        # Remove protocol if passed
        if len(url_sections) > 1:
            url = "".join(url_sections[1:])

        return f"https://{url}{api_path}"

    def login(self, user: str, pwd: str):
        """Authenticates the user with the server. Required for most endpoints

        Args:
            ui (UI): Instance of an implementation of the UI interface
            user (str): Username
            pwd (str): Password
        """
        body = {"username": user, "password": pwd}
        res = self.__req(f"{self.server_url}/auth-token/", requests.post, json=body)
        if res.status_code != 200:
            log_response_error(res)
            raise CommunicationAuthenticationError(
                "Unable to authenticate user with provided credentials"
            )
        else:
            self.token = res.json()["token"]

    def change_password(self, pwd: str):
        """Sets a new password for the current user.

        Args:
            pwd (str): New password to be set
        """
        body = {"password": pwd}
        res = self.__auth_post(f"{self.server_url}/me/password/", json=body)
        if res.status_code != 200:
            log_response_error(res)
            raise CommunicationRequestError("Unable to change the current password")

    def authenticate(self):
        token = read_credentials()
        if token is not None:
            self.token = token
            return

        raise CommunicationAuthenticationError(
            "Couldn't find credentials file. Did you run 'medperf login' before?"
        )

    def __auth_get(self, url, **kwargs):
        return self.__auth_req(url, requests.get, **kwargs)

    def __auth_post(self, url, **kwargs):
        return self.__auth_req(url, requests.post, **kwargs)

    def __auth_put(self, url, **kwargs):
        return self.__auth_req(url, requests.put, **kwargs)

    def __auth_req(self, url, req_func, **kwargs):
        if self.token is None:
            self.authenticate()
        return self.__req(
            url, req_func, headers={"Authorization": f"Token {self.token}"}, **kwargs
        )

    def __req(self, url, req_func, **kwargs):
        logging.debug(f"Calling {req_func}: {url}")
        if "json" in kwargs:
            logging.debug(f"Passing JSON contents: {kwargs['json']}")
            kwargs["json"] = sanitize_json(kwargs["json"])
        try:
            return req_func(url, verify=self.cert, **kwargs)
        except requests.exceptions.SSLError as e:
            logging.error(f"Couldn't connect to {self.server_url}: {e}")
            raise CommunicationError(
                "Couldn't connect to server through HTTPS. If running locally, "
                "remember to provide the server certificate through --certificate"
            )

    def __get_list(
        self,
        url,
        num_elements=None,
        page_size=config.default_page_size,
        offset=0,
        binary_reduction=False,
    ):
        """Retrieves a list of elements from a URL by iterating over pages until num_elements is obtained.
        If num_elements is None, then iterates until all elements have been retrieved.
        If binary_reduction is enabled, errors are assumed to be related to response size. In that case,
        the page_size is reduced by half until a successful response is obtained or until page_size can't be
        reduced anymore.

        Args:
            url (str): The url to retrieve elements from
            num_elements (int, optional): The desired number of elements to be retrieved. Defaults to None.
            page_size (int, optional): Starting page size. Defaults to config.default_page_size.
            start_limit (int, optional): The starting position for element retrieval. Defaults to 0.
            binary_reduction (bool, optional): Wether to handle errors by halfing the page size. Defaults to False.

        Returns:
            List[dict]: A list of dictionaries representing the retrieved elements.
        """
        el_list = []

        if num_elements is None:
            num_elements = float("inf")

        while len(el_list) < num_elements:
            paginated_url = f"{url}?limit={page_size}&offset={offset}"
            res = self.__auth_get(paginated_url)
            if res.status_code != 200:
                if not binary_reduction:
                    log_response_error(res)
                    raise CommunicationRetrievalError(
                        "there was an error retrieving the current list."
                    )

                log_response_error(res, warn=True)
                if page_size <= 1:
                    raise CommunicationRetrievalError(
                        "Could not retrieve list. Minimum page size achieved without success."
                    )
                page_size = page_size // 2
                continue
            else:
                data = res.json()
                el_list += data["results"]
                offset += len(data["results"])
                if data["next"] is None:
                    break

        if type(num_elements) == int:
            return el_list[:num_elements]
        return el_list

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

    def get_benchmarks(self) -> List[dict]:
        """Retrieves all benchmarks in the platform.

        Returns:
            List[dict]: all benchmarks information.
        """
        bmks = self.__get_list(f"{self.server_url}/benchmarks/")
        return bmks

    def get_benchmark(self, benchmark_uid: int) -> dict:
        """Retrieves the benchmark specification file from the server

        Args:
            benchmark_uid (int): uid for the desired benchmark

        Returns:
            dict: benchmark specification
        """
        res = self.__auth_get(f"{self.server_url}/benchmarks/{benchmark_uid}")
        if res.status_code != 200:
            log_response_error(res)
            raise CommunicationRetrievalError("the specified benchmark doesn't exist")
        return res.json()

    def get_benchmark_models(self, benchmark_uid: int) -> List[int]:
        """Retrieves all the models associated with a benchmark. reference model not included

        Args:
            benchmark_uid (int): UID of the desired benchmark

        Returns:
            list[int]: List of model UIDS
        """
        models = self.__get_list(f"{self.server_url}/benchmarks/{benchmark_uid}/models")
        model_uids = [model["id"] for model in models]
        return model_uids

    def get_user_benchmarks(self) -> List[dict]:
        """Retrieves all benchmarks created by the user

        Returns:
            List[dict]: Benchmarks data
        """
        bmks = self.__get_list(f"{self.server_url}/me/benchmarks/")
        return bmks

    def get_cubes(self) -> List[dict]:
        """Retrieves all MLCubes in the platform

        Returns:
            List[dict]: List containing the data of all MLCubes
        """
        cubes = self.__get_list(f"{self.server_url}/mlcubes/")
        return cubes

    def get_cube_metadata(self, cube_uid: int) -> dict:
        """Retrieves metadata about the specified cube

        Args:
            cube_uid (int): UID of the desired cube.

        Returns:
            dict: Dictionary containing url and hashes for the cube files
        """
        res = self.__auth_get(f"{self.server_url}/mlcubes/{cube_uid}/")
        if res.status_code != 200:
            log_response_error(res)
            raise CommunicationRetrievalError("the specified cube doesn't exist")
        return res.json()

    def get_user_cubes(self) -> List[dict]:
        """Retrieves metadata from all cubes registered by the user

        Returns:
            List[dict]: List of dictionaries containing the mlcubes registration information
        """
        cubes = self.__get_list(f"{self.server_url}/me/mlcubes/")
        return cubes

    def upload_benchmark(self, benchmark_dict: dict) -> int:
        """Uploads a new benchmark to the server.

        Args:
            benchmark_dict (dict): benchmark_data to be uploaded

        Returns:
            int: UID of newly created benchmark
        """
        res = self.__auth_post(f"{self.server_url}/benchmarks/", json=benchmark_dict)
        if res.status_code != 201:
            log_response_error(res)
            raise CommunicationRetrievalError("Could not upload benchmark")
        return res.json()

    def upload_mlcube(self, mlcube_body: dict) -> int:
        """Uploads an MLCube instance to the platform

        Args:
            mlcube_body (dict): Dictionary containing all the relevant data for creating mlcubes

        Returns:
            int: id of the created mlcube instance on the platform
        """
        res = self.__auth_post(f"{self.server_url}/mlcubes/", json=mlcube_body)
        if res.status_code != 201:
            log_response_error(res)
            raise CommunicationRetrievalError("Could not upload the mlcube")
        return res.json()

    def get_datasets(self) -> List[dict]:
        """Retrieves all datasets in the platform

        Returns:
            List[dict]: List of data from all datasets
        """
        dsets = self.__get_list(f"{self.server_url}/datasets/")
        return dsets

    def get_dataset(self, dset_uid: int) -> dict:
        """Retrieves a specific dataset

        Args:
            dset_uid (int): Dataset UID

        Returns:
            dict: Dataset metadata
        """
        res = self.__auth_get(f"{self.server_url}/datasets/{dset_uid}/")
        if res.status_code != 200:
            log_response_error(res)
            raise CommunicationRetrievalError(
                "Could not retrieve the specified dataset from server"
            )
        return res.json()

    def get_user_datasets(self) -> dict:
        """Retrieves all datasets registered by the user

        Returns:
            dict: dictionary with the contents of each dataset registration query
        """
        dsets = self.__get_list(f"{self.server_url}/me/datasets/")
        return dsets

    def upload_dataset(self, reg_dict: dict) -> int:
        """Uploads registration data to the server, under the sha name of the file.

        Args:
            reg_dict (dict): Dictionary containing registration information.

        Returns:
            int: id of the created dataset registration.
        """
        res = self.__auth_post(f"{self.server_url}/datasets/", json=reg_dict)
        if res.status_code != 201:
            log_response_error(res)
            raise CommunicationRequestError("Could not upload the dataset")
        return res.json()

    def get_results(self) -> List[dict]:
        """Retrieves all results

        Returns:
            List[dict]: List of results
        """
        res = self.__get_list(f"{self.server_url}/results")
        if res.status_code != 200:
            log_response_error(res)
            raise CommunicationRetrievalError("Could not retrieve results")
        return res.json()

    def get_result(self, result_uid: int) -> dict:
        """Retrieves a specific result data

        Args:
            result_uid (int): Result UID

        Returns:
            dict: Result metadata
        """
        res = self.__auth_get(f"{self.server_url}/results/{result_uid}/")
        if res.status_code != 200:
            log_response_error(res)
            raise CommunicationRetrievalError("Could not retrieve the specified result")
        return res.json()

    def get_user_results(self) -> dict:
        """Retrieves all results registered by the user

        Returns:
            dict: dictionary with the contents of each dataset registration query
        """
        results = self.__get_list(f"{self.server_url}/me/results/")
        return results

    def upload_result(self, results_dict: dict) -> int:
        """Uploads result to the server.

        Args:
            results_dict (dict): Dictionary containing results information.

        Returns:
            int: id of the generated results entry
        """
        res = self.__auth_post(f"{self.server_url}/results/", json=results_dict)
        if res.status_code != 201:
            log_response_error(res)
            raise CommunicationRequestError("Could not upload the results")
        return res.json()

    def associate_dset(self, data_uid: int, benchmark_uid: int, metadata: dict = {}):
        """Create a Dataset Benchmark association

        Args:
            data_uid (int): Registered dataset UID
            benchmark_uid (int): Benchmark UID
            metadata (dict, optional): Additional metadata. Defaults to {}.
        """
        data = {
            "dataset": data_uid,
            "benchmark": benchmark_uid,
            "approval_status": Status.PENDING.value,
            "metadata": metadata,
        }
        res = self.__auth_post(f"{self.server_url}/datasets/benchmarks/", json=data)
        if res.status_code != 201:
            log_response_error(res)
            raise CommunicationRequestError("Could not associate dataset to benchmark")

    def associate_cube(self, cube_uid: int, benchmark_uid: int, metadata: dict = {}):
        """Create an MLCube-Benchmark association

        Args:
            cube_uid (int): MLCube UID
            benchmark_uid (int): Benchmark UID
            metadata (dict, optional): Additional metadata. Defaults to {}.
        """
        data = {
            "approval_status": Status.PENDING.value,
            "model_mlcube": cube_uid,
            "benchmark": benchmark_uid,
            "metadata": metadata,
        }
        res = self.__auth_post(f"{self.server_url}/mlcubes/benchmarks/", json=data)
        if res.status_code != 201:
            log_response_error(res)
            raise CommunicationRequestError("Could not associate mlcube to benchmark")

    def set_dataset_association_approval(
        self, benchmark_uid: int, dataset_uid: int, status: str
    ):
        """Approves a dataset association

        Args:
            dataset_uid (int): Dataset UID
            benchmark_uid (int): Benchmark UID
            status (str): Approval status to set for the association
        """
        url = f"{self.server_url}/datasets/{dataset_uid}/benchmarks/{benchmark_uid}/"
        res = self.__set_approval_status(url, status)
        if res.status_code != 200:
            log_response_error(res)
            raise CommunicationRequestError(
                f"Could not approve association between dataset {dataset_uid} and benchmark {benchmark_uid}"
            )

    def set_mlcube_association_approval(
        self, benchmark_uid: int, mlcube_uid: int, status: str
    ):
        """Approves an mlcube association

        Args:
            mlcube_uid (int): Dataset UID
            benchmark_uid (int): Benchmark UID
            status (str): Approval status to set for the association
        """
        url = f"{self.server_url}/mlcubes/{mlcube_uid}/benchmarks/{benchmark_uid}/"
        res = self.__set_approval_status(url, status)
        if res.status_code != 200:
            log_response_error(res)
            raise CommunicationRequestError(
                f"Could not approve association between mlcube {mlcube_uid} and benchmark {benchmark_uid}"
            )

    def get_datasets_associations(self) -> List[dict]:
        """Get all dataset associations related to the current user

        Returns:
            List[dict]: List containing all associations information
        """
        assocs = self.__get_list(f"{self.server_url}/me/datasets/associations/")
        return assocs

    def get_cubes_associations(self) -> List[dict]:
        """Get all cube associations related to the current user

        Returns:
            List[dict]: List containing all associations information
        """
        assocs = self.__get_list(f"{self.server_url}/me/mlcubes/associations/")
        return assocs

    def set_mlcube_association_priority(
        self, benchmark_uid: int, mlcube_uid: int, priority: int
    ):
        """Sets the priority of an mlcube-benchmark association

        Args:
            mlcube_uid (int): MLCube UID
            benchmark_uid (int): Benchmark UID
            priority (int): priority value to set for the association
        """
        url = f"{self.server_url}/mlcubes/{mlcube_uid}/benchmarks/{benchmark_uid}/"
        data = {"priority": priority}
        res = self.__auth_put(url, json=data,)
        if res.status_code != 200:
            log_response_error(res)
            raise CommunicationRequestError(
                f"Could not set the priority of mlcube {mlcube_uid} within the benchmark {benchmark_uid}"
            )
