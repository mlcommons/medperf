from typing import List, Dict, Union
from abc import ABC, abstractmethod


class Entity(ABC):
    @abstractmethod
    def all(
        cls, local_only: bool = False, comms_func: callable = None
    ) -> List["Entity"]:
        """Gets a list of all instances of the respective entity.
        Wether the list is local or remote depends on the implementation.

        Args:
            local_only (bool, optional): Wether to retrieve only local entities. Defaults to False.
            comms_func (callable, optional): Function to use to retrieve remote entities. If not provided, will use the default entrypoint.

        Returns:
            List[Entity]: a list of entities.
        """

    @abstractmethod
    def get(cls, uid: Union[str, int]) -> "Entity":
        """Gets an instance of the respective entity.
        Wether this requires only local read or remote calls depends
        on the implementation.

        Args:
            uid (str): Unique Identifier to retrieve the entity

        Returns:
            Entity: Entity Instance associated to the UID
        """

    @abstractmethod
    def todict(self) -> Dict:
        """Dictionary representation of the entity

        Returns:
            Dict: Dictionary containing information about the entity
        """

    @abstractmethod
    def upload(self) -> Dict:
        """Upload the entity-related information to the communication's interface

        Returns:
            Dict: Dictionary with the updated entity information
        """

    @abstractmethod
    def write(self) -> str:
        """Writes the entity to the local storage

        Returns:
            str: Path to the stored entity
        """

    @abstractmethod
    def display_dict(self) -> dict:
        """Returns a dictionary of entity properties that can be displayed
        to a user interface using a verbose name of the property rather than
        the internal names

        Returns:
            dict: the display dictionary
        """

    @property
    def identifier(self):
        return self.id or self.generated_uid

    @property
    def is_registered(self):
        return self.id is not None
