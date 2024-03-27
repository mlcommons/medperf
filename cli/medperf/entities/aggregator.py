import os
import yaml
import logging
import hashlib
from typing import List, Optional, Union

from medperf.entities.interface import Entity, Uploadable
from medperf.entities.schemas import MedperfSchema
from medperf.exceptions import (
    InvalidArgumentError,
    MedperfException,
    CommunicationRetrievalError,
)
import medperf.config as config
from medperf.account_management import get_medperf_user_data


class Aggregator(Entity, MedperfSchema, Uploadable):
    """
    Class representing a compatibility test report entry

    A test report is comprised of the components of a test execution:
    - data used, which can be:
        - a demo aggregator url and its hash, or
        - a raw data path and its labels path, or
        - a prepared aggregator uid
    - Data preparation cube if the data used was not already prepared
    - model cube
    - evaluator cube
    - results
    """

    server_config: Optional[dict]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.address = self.server_config["address"]
        self.port = self.server_config["port"]
        self.generated_uid = self.__generate_uid()

        path = config.aggregators_folder
        if self.id:
            path = os.path.join(path, str(self.id))
        else:
            path = os.path.join(path, self.generated_uid)

        self.path = path
        self.network_config_path = os.path.join(path, config.network_config_filename)

    def __generate_uid(self):
        """A helper that generates a unique hash for a server config."""

        params = str(self.server_config)
        return hashlib.sha1(params.encode()).hexdigest()

    def todict(self):
        return self.extended_dict()

    @classmethod
    def all(cls, local_only: bool = False, filters: dict = {}) -> List["Aggregator"]:
        """Gets and creates instances of all the locally prepared aggregators

        Args:
            local_only (bool, optional): Wether to retrieve only local entities. Defaults to False.
            filters (dict, optional): key-value pairs specifying filters to apply to the list of entities.

        Returns:
            List[Aggregator]: a list of Aggregator instances.
        """
        logging.info("Retrieving all aggregators")
        aggs = []
        if not local_only:
            aggs = cls.__remote_all(filters=filters)

        remote_uids = set([agg.id for agg in aggs])

        local_aggs = cls.__local_all()

        aggs += [agg for agg in local_aggs if agg.id not in remote_uids]

        return aggs

    @classmethod
    def __remote_all(cls, filters: dict) -> List["Aggregator"]:
        aggs = []
        try:
            comms_fn = cls.__remote_prefilter(filters)
            aggs_meta = comms_fn()
            aggs = [cls(**meta) for meta in aggs_meta]
        except CommunicationRetrievalError:
            msg = "Couldn't retrieve all aggregators from the server"
            logging.warning(msg)

        return aggs

    @classmethod
    def __remote_prefilter(cls, filters: dict) -> callable:
        """Applies filtering logic that must be done before retrieving remote entities

        Args:
            filters (dict): filters to apply

        Returns:
            callable: A function for retrieving remote entities with the applied prefilters
        """
        comms_fn = config.comms.get_aggregators
        if "owner" in filters and filters["owner"] == get_medperf_user_data()["id"]:
            comms_fn = config.comms.get_user_aggregators
        return comms_fn

    @classmethod
    def __local_all(cls) -> List["Aggregator"]:
        aggs = []
        aggregator_storage = config.aggregators_folder
        try:
            uids = next(os.walk(aggregator_storage))[1]
        except StopIteration:
            msg = "Couldn't iterate over the aggregator directory"
            logging.warning(msg)
            raise MedperfException(msg)

        for uid in uids:
            local_meta = cls.__get_local_dict(uid)
            agg = cls(**local_meta)
            aggs.append(agg)

        return aggs

    @classmethod
    def get(cls, agg_uid: Union[str, int], local_only: bool = False) -> "Aggregator":
        """Retrieves and creates a Aggregator instance from the comms instance.
        If the aggregator is present in the user's machine then it retrieves it from there.

        Args:
            agg_uid (str): server UID of the aggregator

        Returns:
            Aggregator: Specified Aggregator Instance
        """
        if not str(agg_uid).isdigit() or local_only:
            return cls.__local_get(agg_uid)

        try:
            return cls.__remote_get(agg_uid)
        except CommunicationRetrievalError:
            logging.warning(f"Getting Aggregator {agg_uid} from comms failed")
            logging.info(f"Looking for aggregator {agg_uid} locally")
            return cls.__local_get(agg_uid)

    @classmethod
    def __remote_get(cls, agg_uid: int) -> "Aggregator":
        """Retrieves and creates a Aggregator instance from the comms instance.
        If the aggregator is present in the user's machine then it retrieves it from there.

        Args:
            agg_uid (str): server UID of the aggregator

        Returns:
            Aggregator: Specified Aggregator Instance
        """
        logging.debug(f"Retrieving aggregator {agg_uid} remotely")
        meta = config.comms.get_aggregator(agg_uid)
        aggregator = cls(**meta)
        aggregator.write()
        return aggregator

    @classmethod
    def __local_get(cls, agg_uid: Union[str, int]) -> "Aggregator":
        """Retrieves and creates a Aggregator instance from the comms instance.
        If the aggregator is present in the user's machine then it retrieves it from there.

        Args:
            agg_uid (str): server UID of the aggregator

        Returns:
            Aggregator: Specified Aggregator Instance
        """
        logging.debug(f"Retrieving aggregator {agg_uid} locally")
        local_meta = cls.__get_local_dict(agg_uid)
        aggregator = cls(**local_meta)
        return aggregator

    def write(self):
        logging.info(f"Updating registration information for aggregator: {self.id}")
        logging.debug(f"registration information: {self.todict()}")
        regfile = os.path.join(self.path, config.reg_file)
        os.makedirs(self.path, exist_ok=True)
        with open(regfile, "w") as f:
            yaml.dump(self.todict(), f)

        # write network config
        with open(self.network_config_path, "w") as f:
            yaml.dump(self.server_config, f)

        return regfile

    def upload(self):
        """Uploads the registration information to the comms.

        Args:
            comms (Comms): Instance of the comms interface.
        """
        if self.for_test:
            raise InvalidArgumentError("Cannot upload test aggregators.")
        aggregator_dict = self.todict()
        updated_aggregator_dict = config.comms.upload_aggregator(aggregator_dict)
        return updated_aggregator_dict

    @classmethod
    def __get_local_dict(cls, aggregator_uid):
        aggregator_path = os.path.join(
            config.aggregators_folder, str(aggregator_uid)
        )
        regfile = os.path.join(aggregator_path, config.reg_file)
        if not os.path.exists(regfile):
            raise InvalidArgumentError(
                "The requested aggregator information could not be found locally"
            )
        with open(regfile, "r") as f:
            reg = yaml.safe_load(f)
        return reg

    def display_dict(self):
        return {
            "UID": self.identifier,
            "Name": self.name,
            "Generated Hash": self.generated_uid,
            "Address": self.server_config["address"],
            "Port": self.server_config["port"],
            "Created At": self.created_at,
            "Registered": self.is_registered,
        }
