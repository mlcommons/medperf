from typing import List
from abc import ABC, abstractmethod


class Comms(ABC):
    @abstractmethod
    def __init__(self, source: str):
        """Create an instance of a communication object.

        Args:
            source (str): location of the communication source. Where messages are going to be sent.
            ui (UI): Implementation of the UI interface.
            token (str, Optional): authentication token to be used throughout communication. Defaults to None.
        """

    @classmethod
    @abstractmethod
    def parse_url(self, url: str) -> str:
        """Parse the source URL so that it can be used by the comms implementation.
        It should handle protocols and versioning to be able to communicate with the API.

        Args:
            url (str): base URL

        Returns:
            str: parsed URL with protocol and version
        """

    @abstractmethod
    def get_current_user(self):
        """Retrieve the currently-authenticated user information"""

    @abstractmethod
    def get_benchmarks(self) -> List[dict]:
        """Retrieves all benchmarks in the platform.

        Returns:
            List[dict]: all benchmarks information.
        """

    @abstractmethod
    def get_benchmark(self, benchmark_uid: int) -> dict:
        """Retrieves the benchmark specification file from the server

        Args:
            benchmark_uid (int): uid for the desired benchmark

        Returns:
            dict: benchmark specification
        """

    @abstractmethod
    def get_benchmark_model_associations(self, benchmark_uid: int) -> List[int]:
        """Retrieves all the model associations of a benchmark.

        Args:
            benchmark_uid (int): UID of the desired benchmark

        Returns:
            list[int]: List of benchmark model associations
        """

    @abstractmethod
    def get_user_benchmarks(self) -> List[dict]:
        """Retrieves all benchmarks created by the user

        Returns:
            List[dict]: Benchmarks data
        """

    @abstractmethod
    def get_cubes(self) -> List[dict]:
        """Retrieves all MLCubes in the platform

        Returns:
            List[dict]: List containing the data of all MLCubes
        """

    @abstractmethod
    def get_cube_metadata(self, cube_uid: int) -> dict:
        """Retrieves metadata about the specified cube

        Args:
            cube_uid (int): UID of the desired cube.

        Returns:
            dict: Dictionary containing url and hashes for the cube files
        """

    @abstractmethod
    def get_user_cubes(self) -> List[dict]:
        """Retrieves metadata from all cubes registered by the user

        Returns:
            List[dict]: List of dictionaries containing the mlcubes registration information
        """

    @abstractmethod
    def upload_benchmark(self, benchmark_dict: dict) -> int:
        """Uploads a new benchmark to the server.

        Args:
            benchmark_dict (dict): benchmark_data to be uploaded

        Returns:
            int: UID of newly created benchmark
        """

    @abstractmethod
    def upload_mlcube(self, mlcube_body: dict) -> int:
        """Uploads an MLCube instance to the platform

        Args:
            mlcube_body (dict): Dictionary containing all the relevant data for creating mlcubes

        Returns:
            int: id of the created mlcube instance on the platform
        """

    @abstractmethod
    def get_datasets(self) -> List[dict]:
        """Retrieves all datasets in the platform

        Returns:
            List[dict]: List of data from all datasets
        """

    @abstractmethod
    def get_dataset(self, dset_uid: str) -> dict:
        """Retrieves a specific dataset

        Args:
            dset_uid (str): Dataset UID

        Returns:
            dict: Dataset metadata
        """

    @abstractmethod
    def get_user_datasets(self) -> dict:
        """Retrieves all datasets registered by the user

        Returns:
            dict: dictionary with the contents of each dataset registration query
        """

    @abstractmethod
    def upload_dataset(self, reg_dict: dict) -> int:
        """Uploads registration data to the server, under the sha name of the file.

        Args:
            reg_dict (dict): Dictionary containing registration information.

        Returns:
            int: id of the created dataset registration.
        """

    @abstractmethod
    def get_results(self) -> List[dict]:
        """Retrieves all results

        Returns:
            List[dict]: List of results
        """

    @abstractmethod
    def get_result(self, result_uid: str) -> dict:
        """Retrieves a specific result data

        Args:
            result_uid (str): Result UID

        Returns:
            dict: Result metadata
        """

    @abstractmethod
    def get_user_results(self) -> dict:
        """Retrieves all results registered by the user

        Returns:
            dict: dictionary with the contents of each dataset registration query
        """

    @abstractmethod
    def get_benchmark_results(self, benchmark_id: int) -> dict:
        """Retrieves all results for a given benchmark

        Args:
            benchmark_id (int): benchmark ID to retrieve results from

        Returns:
            dict: dictionary with the contents of each result in the specified benchmark
        """

    @abstractmethod
    def upload_result(self, results_dict: dict) -> int:
        """Uploads result to the server.

        Args:
            results_dict (dict): Dictionary containing results information.

        Returns:
            int: id of the generated results entry
        """

    @abstractmethod
    def associate_dset(self, data_uid: int, benchmark_uid: int, metadata: dict = {}):
        """Create a Dataset Benchmark association

        Args:
            data_uid (int): Registered dataset UID
            benchmark_uid (int): Benchmark UID
            metadata (dict, optional): Additional metadata. Defaults to {}.
        """

    @abstractmethod
    def associate_cube(self, cube_uid: str, benchmark_uid: int, metadata: dict = {}):
        """Create an MLCube-Benchmark association

        Args:
            cube_uid (str): MLCube UID
            benchmark_uid (int): Benchmark UID
            metadata (dict, optional): Additional metadata. Defaults to {}.
        """

    @abstractmethod
    def set_dataset_association_approval(
        self, dataset_uid: str, benchmark_uid: str, status: str
    ):
        """Approves a dataset association

        Args:
            dataset_uid (str): Dataset UID
            benchmark_uid (str): Benchmark UID
            status (str): Approval status to set for the association
        """

    @abstractmethod
    def set_mlcube_association_approval(
        self, mlcube_uid: str, benchmark_uid: str, status: str
    ):
        """Approves an mlcube association

        Args:
            mlcube_uid (str): Dataset UID
            benchmark_uid (str): Benchmark UID
            status (str): Approval status to set for the association
        """

    @abstractmethod
    def get_datasets_associations(self) -> List[dict]:
        """Get all dataset associations related to the current user

        Returns:
            List[dict]: List containing all associations information
        """

    @abstractmethod
    def get_cubes_associations(self) -> List[dict]:
        """Get all cube associations related to the current user

        Returns:
            List[dict]: List containing all associations information
        """

    @abstractmethod
    def set_mlcube_association_priority(
        self, benchmark_uid: str, mlcube_uid: str, priority: int
    ):
        """Sets the priority of an mlcube-benchmark association

        Args:
            mlcube_uid (str): MLCube UID
            benchmark_uid (str): Benchmark UID
            priority (int): priority value to set for the association
        """

    @abstractmethod
    def update_dataset(self, dataset_id: int, data: dict):
        """Updates the contents of a datasets identified by dataset_id to the new data dictionary.
        Updates may be partial.

        Args:
            dataset_id (int): ID of the dataset to update
            data (dict): Updated information of the dataset.
        """
