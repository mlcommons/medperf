from typing import List
from abc import ABC, abstractmethod

from medperf.ui import UI
from medperf.enums import Role


class Comms(ABC):
    @abstractmethod
    def __init__(self, source: str, ui: UI, token: str = None):
        """Create an instance of a communication object.

        Args:
            source (str): location of the communication source. Where messages are going to be sent.
            ui (UI): Implementation of the UI interface.
            token (str, Optional): authentication token to be used throughout communication. Defaults to None.
        """

    @abstractmethod
    def login(self, ui: UI):
        """Authenticate the comms instance for further interactions

        Args:
            ui (UI): instance of an implementation of the UI interface.
        """

    @abstractmethod
    def authenticate(self):
        """Retrieve a token stored locally for authentication
        """

    @abstractmethod
    def benchmark_association(self, benchmark_uid: int) -> Role:
        """Retrieves the benchmark association

        Args:
            benchmark_uid (int): UID of the benchmark

        Returns:
            Role: the association type between current user and benchmark
        """

    @abstractmethod
    def authorized_by_role(self, benchmark_uid: int, role: str) -> bool:
        """Indicates wether the current user is authorized to access
        a benchmark based on desired role 

        Args:
            benchmark_uid (int): UID of the benchmark
            role (str): Desired role to check for authorization

        Returns:
            bool: Wether the user has the specified role for that benchmark
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
    def get_benchmark_models(self, benchmark_uid: int) -> List[int]:
        """Retrieves all the models associated with a benchmark. reference model not included

        Args:
            benchmark_uid (int): UID of the desired benchmark

        Returns:
            list[int]: List of model UIDS
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
    def get_cube(self, url: str, cube_uid: int) -> str:
        """Downloads and writes an mlcube.yaml file from the server

        Args:
            url (str): URL where the mlcube.yaml file can be downloaded.
            cube_uid (int): Cube UID.

        Returns:
            str: location where the mlcube.yaml file is stored locally.
        """

    @abstractmethod
    def get_user_cubes(self) -> List[dict]:
        """Retrieves metadata from all cubes registered by the user

        Returns:
            List[dict]: List of dictionaries containing the mlcubes registration information
        """

    @abstractmethod
    def get_cube_params(self, url: str, cube_uid: int) -> str:
        """Retrieves the cube parameters.yaml file from the server

        Args:
            url (str): URL where the parameters.yaml file can be downloaded.
            cube_uid (int): Cube UID.

        Returns:
            str: Location where the parameters.yaml file is stored locally.
        """

    @abstractmethod
    def get_cube_additional(self, url: str, cube_uid: int) -> str:
        """Retrieves and stores the additional_files.tar.gz file from the server

        Args:
            url (str): URL where the additional_files.tar.gz file can be downloaded.
            cube_uid (int): Cube UID.

        Returns:
            str: Location where the additional_files.tar.gz file is stored locally.
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
    def upload_dataset(self, reg_dict: dict) -> int:
        """Uploads registration data to the server, under the sha name of the file.

        Args:
            reg_dict (dict): Dictionary containing registration information.

        Returns:
            int: id of the created dataset registration.
        """

    @abstractmethod
    def upload_results(self, results_dict: dict) -> int:
        """Uploads results to the server.

        Args:
            results_dict (dict): Dictionary containing results information.

        Returns:
            int: id of the generated results entry
        """

    @abstractmethod
    def associate_dset_benchmark(self, data_uid: int, benchmark_uid: int):
        """Create a Dataset Benchmark association

        Args:
            data_uid (int): Registered dataset UID
            benchmark_uid (int): Benchmark UID
        """
