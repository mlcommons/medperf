from typing import List
import requests
import logging

from medperf.enums import Status
import medperf.config as config
from medperf.comms.interface import Comms
from medperf.utils import sanitize_json, log_response_error, format_errors_dict
from medperf.exceptions import (
    CommunicationError,
    CommunicationRetrievalError,
    CommunicationRequestError,
)


class REST(Comms):
    def __init__(self, source: str):
        self.server_url = self.parse_url(source)
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

    def __auth_get(self, url, **kwargs):
        return self.__auth_req(url, requests.get, **kwargs)

    def __auth_post(self, url, **kwargs):
        return self.__auth_req(url, requests.post, **kwargs)

    def __auth_put(self, url, **kwargs):
        return self.__auth_req(url, requests.put, **kwargs)

    def __auth_req(self, url, req_func, **kwargs):
        token = config.auth.access_token
        return self.__req(
            url, req_func, headers={"Authorization": f"Bearer {token}"}, **kwargs
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
        filters={},
        error_msg: str = "",
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
            filters.update({"limit": page_size, "offset": offset})
            query_str = "&".join([f"{k}={v}" for k, v in filters.items()])
            paginated_url = f"{url}?{query_str}"
            res = self.__auth_get(paginated_url)
            if res.status_code != 200:
                if not binary_reduction:
                    log_response_error(res)
                    details = format_errors_dict(res.json())
                    raise CommunicationRetrievalError(f"{error_msg}: {details}")

                log_response_error(res, warn=True)
                details = format_errors_dict(res.json())
                if page_size <= 1:
                    logging.debug(
                        "Could not retrieve list. Minimum page size achieved without success"
                    )
                    raise CommunicationRetrievalError(f"{error_msg}: {details}")
                page_size = page_size // 2
                continue
            else:
                data = res.json()
                el_list += data["results"]
                offset += len(data["results"])
                if data["next"] is None:
                    break

        if isinstance(num_elements, int):
            return el_list[:num_elements]
        return el_list

    def __get(self, url: str, error_msg: str) -> dict:
        """self.__auth_get with error handling"""
        res = self.__auth_get(url)
        if res.status_code != 200:
            log_response_error(res)
            details = format_errors_dict(res.json())
            raise CommunicationRetrievalError(f"{error_msg}: {details}")
        return res.json()

    def __post(self, url: str, json: dict, error_msg: str) -> int:
        """self.__auth_post with error handling"""
        res = self.__auth_post(url, json=json)
        if res.status_code != 201:
            log_response_error(res)
            details = format_errors_dict(res.json())
            raise CommunicationRetrievalError(f"{error_msg}: {details}")
        return res.json()

    def __put(self, url: str, json: dict, error_msg: str):
        """self.__auth_put with error handling"""
        res = self.__auth_put(url, json=json)
        if res.status_code != 200:
            log_response_error(res)
            details = format_errors_dict(res.json())
            raise CommunicationRequestError(f"{error_msg}: {details}")

    def get_current_user(self):
        """Retrieve the currently-authenticated user information"""
        url = f"{self.server_url}/me/"
        error_msg = "Could not get current user"
        return self.__get(url, error_msg)

    # get object
    def get_user(self, user_id: int) -> dict:
        """Retrieves the specified user. This will only return if
        the current user has permission to view the requested user,
        either by being himself, an admin or an owner of a data preparation
        mlcube used by the requested user

        Args:
            user_id (int): User UID

        Returns:
            dict: Requested user information
        """
        url = f"{self.server_url}/users/{user_id}/"
        error_msg = "Could not retrieve user"
        return self.__get(url, error_msg)

    def get_benchmark(self, benchmark_uid: int) -> dict:
        """Retrieves the benchmark specification file from the server

        Args:
            benchmark_uid (int): uid for the desired benchmark

        Returns:
            dict: benchmark specification
        """
        url = f"{self.server_url}/benchmarks/{benchmark_uid}"
        error_msg = "Could not retrieve benchmark"
        return self.__get(url, error_msg)

    def get_cube_metadata(self, cube_uid: int) -> dict:
        """Retrieves metadata about the specified cube

        Args:
            cube_uid (int): UID of the desired cube.

        Returns:
            dict: Dictionary containing url and hashes for the cube files
        """
        url = f"{self.server_url}/mlcubes/{cube_uid}/"
        error_msg = "Could not retrieve mlcube"
        return self.__get(url, error_msg)

    def get_container_ca(self, cube_uid: int) -> dict:
        """Retrieves the cube's ca object from the server

        Args:
            cube_uid (int): uid for the model

        Returns:
            dict: ca specification
        """
        url = f"{self.server_url}/mlcubes/{cube_uid}/ca/"
        error_msg = "Could not retrieve Certificate Authority (CA) associated with this container."
        return self.__get(url, error_msg)

    def get_dataset(self, dset_uid: int) -> dict:
        """Retrieves a specific dataset

        Args:
            dset_uid (int): Dataset UID

        Returns:
            dict: Dataset metadata
        """
        url = f"{self.server_url}/datasets/{dset_uid}/"
        error_msg = "Could not retrieve dataset"
        return self.__get(url, error_msg)

    def get_execution(self, execution_uid: int) -> dict:
        """Retrieves a specific execution data

        Args:
            execution_uid (int): Execution UID

        Returns:
            dict: Execution metadata
        """
        url = f"{self.server_url}/results/{execution_uid}/"
        error_msg = "Could not retrieve execution"
        return self.__get(url, error_msg)

    def get_training_exp(self, training_exp_id: int) -> dict:
        """Retrieves the training_exp specification file from the server

        Args:
            training_exp_id (int): uid for the desired training_exp

        Returns:
            dict: training_exp specification
        """
        url = f"{self.server_url}/training/{training_exp_id}/"
        error_msg = "Could not retrieve training experiment"
        return self.__get(url, error_msg)

    def get_aggregator(self, aggregator_id: int) -> dict:
        """Retrieves the aggregator specification file from the server

        Args:
            benchmark_uid (int): uid for the desired benchmark

        Returns:
            dict: benchmark specification
        """
        url = f"{self.server_url}/aggregators/{aggregator_id}"
        error_msg = "Could not retrieve aggregator"
        return self.__get(url, error_msg)

    def get_ca(self, ca_id: int) -> dict:
        """Retrieves the aggregator specification file from the server

        Args:
            benchmark_uid (int): uid for the desired benchmark

        Returns:
            dict: benchmark specification
        """
        url = f"{self.server_url}/cas/{ca_id}"
        error_msg = "Could not retrieve ca"
        return self.__get(url, error_msg)

    def get_training_event(self, event_id: int) -> dict:
        """Retrieves the aggregator specification file from the server

        Args:
            benchmark_uid (int): uid for the desired benchmark

        Returns:
            dict: benchmark specification
        """
        url = f"{self.server_url}/training/events/{event_id}"
        error_msg = "Could not retrieve training event"
        return self.__get(url, error_msg)

    # get object of an object
    def get_experiment_event(self, training_exp_id: int) -> dict:
        """Retrieves the training experiment's event object from the server

        Args:
            training_exp_id (int): uid for the training experiment

        Returns:
            dict: event specification
        """
        url = f"{self.server_url}/training/{training_exp_id}/event/"
        error_msg = "Could not retrieve training experiment event"
        return self.__get(url, error_msg)

    def get_experiment_aggregator(self, training_exp_id: int) -> dict:
        """Retrieves the training experiment's aggregator object from the server

        Args:
            training_exp_id (int): uid for the training experiment

        Returns:
            dict: aggregator specification
        """
        url = f"{self.server_url}/training/{training_exp_id}/aggregator/"
        error_msg = "Could not retrieve training experiment aggregator"
        return self.__get(url, error_msg)

    def get_experiment_ca(self, training_exp_id: int) -> dict:
        """Retrieves the training experiment's ca object from the server

        Args:
            training_exp_id (int): uid for the training experiment

        Returns:
            dict: ca specification
        """
        url = f"{self.server_url}/training/{training_exp_id}/ca/"
        error_msg = "Could not retrieve training experiment ca"
        return self.__get(url, error_msg)

    # get list
    def get_benchmarks(self, filters={}) -> List[dict]:
        """Retrieves all benchmarks in the platform.

        Returns:
            List[dict]: all benchmarks information.
        """
        url = f"{self.server_url}/benchmarks/"
        error_msg = "Could not retrieve benchmarks"
        return self.__get_list(url, filters=filters, error_msg=error_msg)

    def get_cubes(self, filters={}) -> List[dict]:
        """Retrieves all MLCubes in the platform

        Returns:
            List[dict]: List containing the data of all MLCubes
        """
        url = f"{self.server_url}/mlcubes/"
        error_msg = "Could not retrieve mlcubes"
        return self.__get_list(url, filters=filters, error_msg=error_msg)

    def get_datasets(self, filters={}) -> List[dict]:
        """Retrieves all datasets in the platform

        Returns:
            List[dict]: List of data from all datasets
        """
        url = f"{self.server_url}/datasets/"
        error_msg = "Could not retrieve datasets"
        return self.__get_list(url, filters=filters, error_msg=error_msg)

    def get_executions(self, filters={}) -> List[dict]:
        """Retrieves all executions

        Returns:
            List[dict]: List of executions
        """
        url = f"{self.server_url}/results/"
        error_msg = "Could not retrieve executions"
        return self.__get_list(url, filters=filters, error_msg=error_msg)

    def get_training_exps(self, filters={}) -> List[dict]:
        """Retrieves all training_exps

        Returns:
            List[dict]: List of training_exps
        """
        url = f"{self.server_url}/training/"
        error_msg = "Could not retrieve training experiments"
        return self.__get_list(url, filters=filters, error_msg=error_msg)

    def get_aggregators(self, filters={}) -> List[dict]:
        """Retrieves all aggregators

        Returns:
            List[dict]: List of aggregators
        """
        url = f"{self.server_url}/aggregators/"
        error_msg = "Could not retrieve aggregators"
        return self.__get_list(url, filters=filters, error_msg=error_msg)

    def get_cas(self, filters={}) -> List[dict]:
        """Retrieves all cas

        Returns:
            List[dict]: List of cas
        """
        url = f"{self.server_url}/cas/"
        error_msg = "Could not retrieve cas"
        return self.__get_list(url, filters=filters, error_msg=error_msg)

    def get_training_events(self, filters={}) -> List[dict]:
        """Retrieves all training events

        Returns:
            List[dict]: List of training events
        """
        url = f"{self.server_url}/training/events/"
        error_msg = "Could not retrieve training events"
        return self.__get_list(url, filters=filters, error_msg=error_msg)

    # get user list
    def get_user_cubes(self, filters={}) -> List[dict]:
        """Retrieves metadata from all cubes registered by the user

        Returns:
            List[dict]: List of dictionaries containing the mlcubes registration information
        """
        url = f"{self.server_url}/me/mlcubes/"
        error_msg = "Could not retrieve user mlcubes"
        return self.__get_list(url, filters=filters, error_msg=error_msg)

    def get_user_datasets(self, filters={}) -> dict:
        """Retrieves all datasets registered by the user

        Returns:
            dict: dictionary with the contents of each dataset registration query
        """
        url = f"{self.server_url}/me/datasets/"
        error_msg = "Could not retrieve user datasets"
        return self.__get_list(url, filters=filters, error_msg=error_msg)

    def get_user_benchmarks(self, filters={}) -> List[dict]:
        """Retrieves all benchmarks created by the user

        Returns:
            List[dict]: Benchmarks data
        """
        url = f"{self.server_url}/me/benchmarks/"
        error_msg = "Could not retrieve user benchmarks"
        return self.__get_list(url, filters=filters, error_msg=error_msg)

    def get_user_executions(self, filters={}) -> dict:
        """Retrieves all executions registered by the user

        Returns:
            dict: dictionary with the contents of each execution registration query
        """
        url = f"{self.server_url}/me/results/"
        error_msg = "Could not retrieve user executions"
        return self.__get_list(url, filters=filters, error_msg=error_msg)

    def get_user_training_exps(self, filters={}) -> dict:
        """Retrieves all training_exps registered by the user

        Returns:
            dict: dictionary with the contents of each result registration query
        """
        url = f"{self.server_url}/me/training/"
        error_msg = "Could not retrieve user training experiments"
        return self.__get_list(url, filters=filters, error_msg=error_msg)

    def get_user_aggregators(self, filters={}) -> dict:
        """Retrieves all aggregators registered by the user

        Returns:
            dict: dictionary with the contents of each result registration query
        """
        url = f"{self.server_url}/me/aggregators/"
        error_msg = "Could not retrieve user aggregators"
        return self.__get_list(url, filters=filters, error_msg=error_msg)

    def get_user_cas(self, filters={}) -> dict:
        """Retrieves all cas registered by the user

        Returns:
            dict: dictionary with the contents of each result registration query
        """
        url = f"{self.server_url}/me/cas/"
        error_msg = "Could not retrieve user cas"
        return self.__get_list(url, filters=filters, error_msg=error_msg)

    def get_user_training_events(self, filters={}) -> dict:
        """Retrieves all training events registered by the user

        Returns:
            dict: dictionary with the contents of each result registration query
        """
        url = f"{self.server_url}/me/training/events/"
        error_msg = "Could not retrieve user training events"
        return self.__get_list(url, filters=filters, error_msg=error_msg)

    # get user associations list
    def get_user_benchmarks_datasets_associations(self, filters={}) -> List[dict]:
        """Get all dataset associations related to the current user

        Returns:
            List[dict]: List containing all associations information
        """
        url = f"{self.server_url}/me/datasets/associations/"
        error_msg = "Could not retrieve user datasets benchmark associations"
        return self.__get_list(url, filters=filters, error_msg=error_msg)

    def get_user_benchmarks_models_associations(self, filters={}) -> List[dict]:
        """Get all cube associations related to the current user

        Returns:
            List[dict]: List containing all associations information
        """
        url = f"{self.server_url}/me/mlcubes/associations/"
        error_msg = "Could not retrieve user mlcubes benchmark associations"
        return self.__get_list(url, filters=filters, error_msg=error_msg)

    def get_user_training_datasets_associations(self, filters={}) -> List[dict]:
        """Get all training dataset associations related to the current user

        Returns:
            List[dict]: List containing all associations information
        """
        url = f"{self.server_url}/me/datasets/training_associations/"
        error_msg = "Could not retrieve user datasets training associations"
        return self.__get_list(url, filters=filters, error_msg=error_msg)

    def get_user_training_aggregators_associations(self, filters={}) -> List[dict]:
        """Get all aggregator associations related to the current user

        Returns:
            List[dict]: List containing all associations information
        """
        url = f"{self.server_url}/me/aggregators/training_associations/"
        error_msg = "Could not retrieve user aggregators training associations"
        return self.__get_list(url, filters=filters, error_msg=error_msg)

    def get_user_training_cas_associations(self, filters={}) -> List[dict]:
        """Get all ca associations related to the current user

        Returns:
            List[dict]: List containing all associations information
        """
        url = f"{self.server_url}/me/cas/training_associations/"
        error_msg = "Could not retrieve user cas training associations"
        return self.__get_list(url, filters=filters, error_msg=error_msg)

    # upload
    def upload_benchmark(self, benchmark_dict: dict) -> int:
        """Uploads a new benchmark to the server.

        Args:
            benchmark_dict (dict): benchmark_data to be uploaded

        Returns:
            int: UID of newly created benchmark
        """
        url = f"{self.server_url}/benchmarks/"
        error_msg = "could not upload benchmark"
        return self.__post(url, json=benchmark_dict, error_msg=error_msg)

    def upload_mlcube(self, mlcube_body: dict) -> int:
        """Uploads an MLCube instance to the platform

        Args:
            mlcube_body (dict): Dictionary containing all the relevant data for creating mlcubes

        Returns:
            int: id of the created mlcube instance on the platform
        """
        url = f"{self.server_url}/mlcubes/"
        error_msg = "could not upload mlcube"
        return self.__post(url, json=mlcube_body, error_msg=error_msg)

    def upload_dataset(self, reg_dict: dict) -> int:
        """Uploads registration data to the server, under the sha name of the file.

        Args:
            reg_dict (dict): Dictionary containing registration information.

        Returns:
            int: id of the created dataset registration.
        """
        url = f"{self.server_url}/datasets/"
        error_msg = "could not upload dataset"
        return self.__post(url, json=reg_dict, error_msg=error_msg)

    def upload_execution(self, executions_dict: dict) -> int:
        """Uploads execution to the server.

        Args:
            executions_dict (dict): Dictionary containing executions information.

        Returns:
            dict: generated executions entry
        """
        url = f"{self.server_url}/results/"
        error_msg = "could not upload execution"
        return self.__post(url, json=executions_dict, error_msg=error_msg)

    def update_execution(self, execution_id: int, data: dict) -> dict:
        """Updates an execution object
        Args:
            execution_id (int): Execution ID
            data (dict): Execution data. Can be a partial update
        Returns:
            dict: Updated description of the execution
        """
        url = f"{self.server_url}/results/{execution_id}/"
        error_msg = "Could not update execution"
        return self.__put(url, json=data, error_msg=error_msg)

    def upload_training_exp(self, training_exp_dict: dict) -> int:
        """Uploads a new training_exp to the server.

        Args:
            training_exp_dict (dict): training_exp to be uploaded

        Returns:
            dict: newly created training_exp
        """
        url = f"{self.server_url}/training/"
        error_msg = "could not upload training experiment"
        return self.__post(url, json=training_exp_dict, error_msg=error_msg)

    def upload_aggregator(self, aggregator_dict: dict) -> int:
        """Uploads a new aggregator to the server.

        Args:
            benchmark_dict (dict): benchmark_data to be uploaded

        Returns:
            int: UID of newly created benchmark
        """
        url = f"{self.server_url}/aggregators/"
        error_msg = "could not upload aggregator"
        return self.__post(url, json=aggregator_dict, error_msg=error_msg)

    def upload_ca(self, ca_dict: dict) -> int:
        """Uploads a new ca to the server.

        Args:
            benchmark_dict (dict): benchmark_data to be uploaded

        Returns:
            int: UID of newly created benchmark
        """
        url = f"{self.server_url}/cas/"
        error_msg = "could not upload ca"
        return self.__post(url, json=ca_dict, error_msg=error_msg)

    def upload_training_event(self, trainnig_event_dict: dict) -> int:
        """Uploads a new training event to the server.

        Args:
            benchmark_dict (dict): benchmark_data to be uploaded

        Returns:
            int: UID of newly created benchmark
        """
        url = f"{self.server_url}/training/events/"
        error_msg = "could not upload training event"
        return self.__post(url, json=trainnig_event_dict, error_msg=error_msg)

    # Association creation
    def associate_benchmark_dataset(
        self, data_uid: int, benchmark_uid: int, metadata: dict = {}
    ):
        """Create a Dataset Benchmark association

        Args:
            data_uid (int): Registered dataset UID
            benchmark_uid (int): Benchmark UID
            metadata (dict, optional): Additional metadata. Defaults to {}.
        """
        url = f"{self.server_url}/datasets/benchmarks/"
        data = {
            "dataset": data_uid,
            "benchmark": benchmark_uid,
            "approval_status": Status.PENDING.value,
            "metadata": metadata,
        }
        error_msg = "Could not associate dataset to benchmark"
        return self.__post(url, json=data, error_msg=error_msg)

    def associate_benchmark_model(
        self, cube_uid: int, benchmark_uid: int, metadata: dict = {}
    ):
        """Create an MLCube-Benchmark association

        Args:
            cube_uid (int): MLCube UID
            benchmark_uid (int): Benchmark UID
            metadata (dict, optional): Additional metadata. Defaults to {}.
        """
        url = f"{self.server_url}/mlcubes/benchmarks/"
        data = {
            "approval_status": Status.PENDING.value,
            "model_mlcube": cube_uid,
            "benchmark": benchmark_uid,
            "metadata": metadata,
        }
        error_msg = "Could not associate mlcube to benchmark"
        return self.__post(url, json=data, error_msg=error_msg)

    def associate_ca_model(self, cube_uid: int, ca_uid: int, metadata: dict = None):
        """Create an MLCube-CA association

        Args:
            cube_uid (int): MLCube UID
            ca_uid (int): CA UID
            metadata (dict, optional): Additional metadata. Defaults to {}.
        """
        metadata = metadata or {}
        url = f"{self.server_url}/mlcubes/{cube_uid}/ca/"
        data = {
            "model_mlcube": cube_uid,
            "associated_ca": ca_uid,
            "metadata": metadata,
        }
        error_msg = "Could not associate mlcube to ca"
        return self.__post(url, json=data, error_msg=error_msg)

    def associate_training_dataset(self, data_uid: int, training_exp_id: int):
        """Create a Dataset experiment association

        Args:
            data_uid (int): Registered dataset UID
            benchmark_uid (int): Benchmark UID
            metadata (dict, optional): Additional metadata. Defaults to {}.
        """
        url = f"{self.server_url}/datasets/training/"
        data = {
            "dataset": data_uid,
            "training_exp": training_exp_id,
            "approval_status": Status.PENDING.value,
        }
        error_msg = "Could not associate dataset to training_exp"
        return self.__post(url, json=data, error_msg=error_msg)

    def associate_training_aggregator(self, aggregator_id: int, training_exp_id: int):
        """Create a aggregator experiment association

        Args:
            aggregator_id (int): Registered aggregator UID
            training_exp_id (int): training experiment UID
        """
        url = f"{self.server_url}/aggregators/training/"
        data = {
            "aggregator": aggregator_id,
            "training_exp": training_exp_id,
            "approval_status": Status.PENDING.value,
        }
        error_msg = "Could not associate aggregator to training_exp"
        return self.__post(url, json=data, error_msg=error_msg)

    def associate_container_ca(self, ca_id: int, container_id: int):
        """Create a ca experiment association

        Args:
            ca_id (int): Registered ca UID
            containr_id (int): Container (MLCube) UID
        """
        url = f"{self.server_url}/cas/mlcube/"
        data = {
            "ca": ca_id,
            "mlcube": container_id,
            "approval_status": Status.PENDING.value,
        }
        error_msg = "Could not associate ca to container"
        return self.__post(url, json=data, error_msg=error_msg)

    def associate_training_ca(self, ca_id: int, training_exp_id: int):
        """Create a ca experiment association

        Args:
            ca_id (int): Registered ca UID
            training_exp_id (int): training experiment UID
        """
        url = f"{self.server_url}/cas/training/"
        data = {
            "ca": ca_id,
            "training_exp": training_exp_id,
            "approval_status": Status.PENDING.value,
        }
        error_msg = "Could not associate ca to training_exp"
        return self.__post(url, json=data, error_msg=error_msg)

    # updates associations
    def update_benchmark_dataset_association(
        self, benchmark_uid: int, dataset_uid: int, data: str
    ):
        """Approves a dataset association

        Args:
            dataset_uid (int): Dataset UID
            benchmark_uid (int): Benchmark UID
            status (str): Approval status to set for the association
        """
        url = f"{self.server_url}/datasets/{dataset_uid}/benchmarks/{benchmark_uid}/"
        error_msg = f"Could not update association: dataset {dataset_uid}, benchmark {benchmark_uid}"
        self.__put(url, json=data, error_msg=error_msg)

    def update_benchmark_model_association(
        self, benchmark_uid: int, mlcube_uid: int, data: dict
    ):
        """Approves an mlcube association

        Args:
            mlcube_uid (int): Dataset UID
            benchmark_uid (int): Benchmark UID
            status (str): Approval status to set for the association
        """
        url = f"{self.server_url}/mlcubes/{mlcube_uid}/benchmarks/{benchmark_uid}/"
        error_msg = (
            f"Could update association: mlcube {mlcube_uid}, benchmark {benchmark_uid}"
        )
        self.__put(url, json=data, error_msg=error_msg)

    def update_training_aggregator_association(
        self, training_exp_id: int, aggregator_id: int, data: dict
    ):
        """Approves a aggregator association

        Args:
            dataset_uid (int): Dataset UID
            benchmark_uid (int): Benchmark UID
            status (str): Approval status to set for the association
        """
        url = (
            f"{self.server_url}/aggregators/{aggregator_id}/training/{training_exp_id}/"
        )
        error_msg = (
            "Could not update association: aggregator"
            f" {aggregator_id}, training_exp {training_exp_id}"
        )
        self.__put(url, json=data, error_msg=error_msg)

    def update_training_dataset_association(
        self, training_exp_id: int, dataset_uid: int, data: dict
    ):
        """Approves a training dataset association

        Args:
            dataset_uid (int): Dataset UID
            benchmark_uid (int): Benchmark UID
            status (str): Approval status to set for the association
        """
        url = f"{self.server_url}/datasets/{dataset_uid}/training/{training_exp_id}/"
        error_msg = (
            "Could not approve association: dataset"
            f"{dataset_uid}, training_exp {training_exp_id}"
        )
        self.__put(url, json=data, error_msg=error_msg)

    def update_training_ca_association(
        self, training_exp_id: int, ca_uid: int, data: dict
    ):
        """Approves a training ca association

        Args:
            dataset_uid (int): Dataset UID
            benchmark_uid (int): Benchmark UID
            status (str): Approval status to set for the association
        """
        url = f"{self.server_url}/cas/{ca_uid}/training/{training_exp_id}/"
        error_msg = (
            f"Could not update association: ca{ca_uid}, training_exp {training_exp_id}"
        )
        self.__put(url, json=data, error_msg=error_msg)

    # update objects
    def update_dataset(self, dataset_id: int, data: dict):
        url = f"{self.server_url}/datasets/{dataset_id}/"
        error_msg = "Could not update dataset"
        return self.__put(url, json=data, error_msg=error_msg)

    def update_training_exp(self, training_exp_id: int, data: dict):
        url = f"{self.server_url}/training/{training_exp_id}/"
        error_msg = "Could not update training experiment"
        return self.__put(url, json=data, error_msg=error_msg)

    def update_training_event(self, training_event_id: int, data: dict):
        url = f"{self.server_url}/training/events/{training_event_id}/"
        error_msg = "Could not update training event"
        return self.__put(url, json=data, error_msg=error_msg)

    def update_benchmark(self, benchmark_id: int, data: dict):
        url = f"{self.server_url}/benchmarks/{benchmark_id}/"
        error_msg = "Could not update benchmark"
        return self.__put(url, json=data, error_msg=error_msg)

    # misc
    def get_benchmark_executions(self, benchmark_id: int, filters={}) -> dict:
        """Retrieves all executions for a given benchmark

        Args:
            benchmark_id (int): benchmark ID to retrieve executions from

        Returns:
            dict: dictionary with the contents of each execution in the specified benchmark
        """
        url = f"{self.server_url}/benchmarks/{benchmark_id}/results/"
        error_msg = "Could not get benchmark executions"
        return self.__get_list(url, filters=filters, error_msg=error_msg)

    def get_mlcube_datasets(self, mlcube_id: int, filters={}) -> dict:
        """Retrieves all datasets that have the specified mlcube as the prep mlcube

        Args:
            mlcube_id (int): mlcube ID to retrieve datasets from

        Returns:
            dict: dictionary with the contents of each dataset
        """
        url = f"{self.server_url}/mlcubes/{mlcube_id}/datasets/"
        error_msg = "Could not get mlcube datasets"
        return self.__get_list(url, filters=filters, error_msg=error_msg)

    def get_training_datasets_associations(
        self, training_exp_id: int, filters={}
    ) -> dict:
        """Retrieves all datasets for a given training_exp

        Args:
            benchmark_id (int): benchmark ID to retrieve results from

        Returns:
            dict: dictionary with the contents of each result in the specified benchmark
        """
        url = f"{self.server_url}/training/{training_exp_id}/datasets"
        error_msg = "Could not get training experiment datasets associations"
        return self.__get_list(url, filters=filters, error_msg=error_msg)

    def get_benchmark_models_associations(
        self, benchmark_uid: int, filters={}
    ) -> List[int]:
        """Retrieves all the model associations of a benchmark.

        Args:
            benchmark_uid (int): UID of the desired benchmark

        Returns:
            list[int]: List of benchmark model associations
        """
        url = f"{self.server_url}/benchmarks/{benchmark_uid}/models"
        error_msg = "Could not get benchmark models associations"
        return self.__get_list(url, filters=filters, error_msg=error_msg)

    def get_training_datasets_with_users(
        self, training_exp_id: int, filters={}
    ) -> dict:
        """Retrieves all datasets for a given training_exp and their owner information

        Args:
            training_exp_id (int): training exp ID

        Returns:
            dict: dictionary with the contents of dataset IDs and owner info
        """
        url = f"{self.server_url}/training/{training_exp_id}/participants_info/"
        error_msg = "Could not get training experiment participants info"
        return self.__get_list(url, filters=filters, error_msg=error_msg)

    def get_benchmark_datasets_with_users(self, benchmark_id: int, filters={}) -> dict:
        """Retrieves all datasets for a given benchmark and their owner information

        Args:
            benchmark_id (int): benchmark ID

        Returns:
            dict: dictionary with the contents of dataset IDs and owner info
        """
        url = f"{self.server_url}/benchmarks/{benchmark_id}/participants_info/"
        error_msg = "Could not get benchmark participants info"
        return self.__get_list(url, filters=filters, error_msg=error_msg)
