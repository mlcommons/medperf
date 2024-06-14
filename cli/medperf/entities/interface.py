import shutil
from typing import List, Dict, Union, Callable
from abc import ABC
import logging
import os
import yaml
from medperf.exceptions import MedperfException, InvalidArgumentError
from medperf.entities.schemas import MedperfSchema
from typing import Type, TypeVar

EntityType = TypeVar("EntityType", bound="Entity")


class Entity(MedperfSchema, ABC):
    @staticmethod
    def get_type() -> str:
        raise NotImplementedError()

    @staticmethod
    def get_storage_path() -> str:
        raise NotImplementedError()

    @staticmethod
    def get_comms_retriever() -> Callable[[int], dict]:
        raise NotImplementedError()

    @staticmethod
    def get_metadata_filename() -> str:
        raise NotImplementedError()

    @staticmethod
    def get_comms_uploader() -> Callable[[dict], dict]:
        raise NotImplementedError()

    @property
    def local_id(self) -> str:
        raise NotImplementedError()

    @property
    def identifier(self) -> Union[int, str]:
        return self.id or self.local_id

    @property
    def is_registered(self) -> bool:
        return self.id is not None

    @property
    def path(self) -> str:
        storage_path = self.get_storage_path()
        return os.path.join(storage_path, str(self.identifier))

    @classmethod
    def all(
        cls: Type[EntityType], unregistered: bool = False, filters: dict = {}
    ) -> List[EntityType]:
        """Gets a list of all instances of the respective entity.
        Whether the list is local or remote depends on the implementation.

        Args:
            unregistered (bool, optional): Wether to retrieve only unregistered local entities. Defaults to False.
            filters (dict, optional): key-value pairs specifying filters to apply to the list of entities.


        Returns:
            List[Entity]: a list of entities.
        """
        logging.info(f"Retrieving all {cls.get_type()} entities")
        if unregistered:
            if filters:
                raise InvalidArgumentError(
                    "Filtering is not supported for unregistered entities"
                )
            return cls.__unregistered_all()
        return cls.__remote_all(filters=filters)

    @classmethod
    def __remote_all(cls: Type[EntityType], filters: dict) -> List[EntityType]:
        comms_fn = cls.remote_prefilter(filters)
        entity_meta = comms_fn()
        entities = [cls(**meta) for meta in entity_meta]
        return entities

    @classmethod
    def __unregistered_all(cls: Type[EntityType]) -> List[EntityType]:
        entities = []
        storage_path = cls.get_storage_path()
        try:
            uids = next(os.walk(storage_path))[1]
        except StopIteration:
            msg = f"Couldn't iterate over the {cls.get_type()} storage"
            logging.warning(msg)
            raise MedperfException(msg)

        for uid in uids:
            if uid.isdigit():
                continue
            entity = cls.__local_get(uid)
            entities.append(entity)

        return entities

    @staticmethod
    def remote_prefilter(filters: dict) -> callable:
        """Applies filtering logic that must be done before retrieving remote entities

        Args:
            filters (dict): filters to apply

        Returns:
            callable: A function for retrieving remote entities with the applied prefilters
        """
        raise NotImplementedError

    @classmethod
    def get(
        cls: Type[EntityType], uid: Union[str, int], local_only: bool = False
    ) -> EntityType:
        """Gets an instance of the respective entity.
        Wether this requires only local read or remote calls depends
        on the implementation.

        Args:
            uid (str): Unique Identifier to retrieve the entity
            local_only (bool): If True, the entity will be retrieved locally

        Returns:
            Entity: Entity Instance associated to the UID
        """

        if not str(uid).isdigit() or local_only:
            return cls.__local_get(uid)
        return cls.__remote_get(uid)

    @classmethod
    def __remote_get(cls: Type[EntityType], uid: int) -> EntityType:
        """Retrieves and creates an entity instance from the comms instance.

        Args:
            uid (int): server UID of the entity

        Returns:
            Entity: Specified Entity Instance
        """
        logging.debug(f"Retrieving {cls.get_type()} {uid} remotely")
        comms_func = cls.get_comms_retriever()
        entity_dict = comms_func(uid)
        entity = cls(**entity_dict)
        entity.write()
        return entity

    @classmethod
    def __local_get(cls: Type[EntityType], uid: Union[str, int]) -> EntityType:
        """Retrieves and creates an entity instance from the local storage.

        Args:
            uid (str|int): UID of the entity

        Returns:
            Entity: Specified Entity Instance
        """
        logging.debug(f"Retrieving {cls.get_type()} {uid} locally")
        entity_dict = cls.__get_local_dict(uid)
        entity = cls(**entity_dict)
        return entity

    @classmethod
    def __get_local_dict(cls: Type[EntityType], uid: Union[str, int]) -> dict:
        """Retrieves a local entity information

        Args:
            uid (str): uid of the local entity

        Returns:
            dict: information of the entity
        """
        logging.info(f"Retrieving {cls.get_type()} {uid} from local storage")
        storage_path = cls.get_storage_path()
        metadata_filename = cls.get_metadata_filename()
        entity_file = os.path.join(storage_path, str(uid), metadata_filename)
        if not os.path.exists(entity_file):
            raise InvalidArgumentError(
                f"No {cls.get_type()} with the given uid could be found"
            )
        with open(entity_file, "r") as f:
            data = yaml.safe_load(f)

        return data

    def write(self) -> str:
        """Writes the entity to the local storage

        Returns:
            str: Path to the stored entity
        """
        data = self.todict()
        metadata_filename = self.get_metadata_filename()
        entity_file = os.path.join(self.path, metadata_filename)
        os.makedirs(self.path, exist_ok=True)
        with open(entity_file, "w") as f:
            yaml.dump(data, f)
        return entity_file

    def remove_from_filesystem(self):
        """Removes the entity folder recursively from the local storage"""
        # TODO: might be dangerous
        shutil.rmtree(self.path, ignore_errors=True)

    def upload(self) -> Dict:
        """Upload the entity-related information to the communication's interface

        Returns:
            Dict: Dictionary with the updated entity information
        """
        if self.for_test:
            raise InvalidArgumentError(
                f"This test {self.get_type()} cannot be uploaded."
            )
        body = self.todict()
        comms_func = self.get_comms_uploader()
        updated_body = comms_func(body)
        return updated_body

    def display_dict(self) -> dict:
        """Returns a dictionary of entity properties that can be displayed
        to a user interface using a verbose name of the property rather than
        the internal names

        Returns:
            dict: the display dictionary
        """
        raise NotImplementedError
