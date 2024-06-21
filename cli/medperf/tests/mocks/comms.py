# Utility functions for mocking comms and its methods
from typing import Dict, List, Callable, Union, TypeVar, Tuple
from unittest.mock import MagicMock
from pytest_mock.plugin import MockFixture
from medperf.exceptions import CommunicationRetrievalError


class TestEntityStorage:
    AnyEntity = TypeVar("AnyEntity")

    def __init__(self,
                 generate_fun: Callable[[Dict], AnyEntity],
                 ents: Dict[str, Dict]):

        self.storage = ents
        self.uploaded = []
        self.generate_fun = generate_fun  # 🥳  <- generated fun

    def get(self, id_) -> Dict:
        if id_ not in self.storage:
            raise CommunicationRetrievalError(f"Get entity {id_}: not found in test storage")
        return self.storage[id_]

    def upload(self, ent: Dict) -> Dict:
        id_ = ent["id"]
        if id_ is None or id_ == "":  # not include 0 as 0 is a valid id
            id_ = str(-len(self.storage))  # some non-existent id
            assert id_ not in self.storage, f"Upload failed: generated id {id_} already exists in storage"
        self.storage[id_] = self.generate_fun(**ent).todict()
        self.uploaded.append(ent)
        return self.storage[id_]

    def edit(self, ent: Dict):
        id_ = ent["id"]
        if id_ not in self.storage:
            raise CommunicationRetrievalError(f"Edit entity {id_}: not found in test storage")
        orig_value = self.storage[id_]
        new_value = {**orig_value, **ent}  # rewrites all fields from ent
        self.storage[id_] = new_value


def mock_comms_entity_gets(
    mocker: MockFixture,
    comms: MagicMock,
    generate_fn: Callable,
    comms_calls: Dict[str, str],
    all_ents: List[Union[str, Dict]],
    user_ents: List[Union[str, Dict]],
) -> TestEntityStorage:
    """Mocks API endpoints used by an entity instance. Allows to define
    what is returned by each endpoint, and keeps track of submitted instances.

    Args:
        mocker (pytest_mock.plugin.MockFixture): Mocker object
        comms (unittest.mock.MagicMock): A mocked comms instance
        generate_fn (Callable): A function that generates entity dictionaries
        comms_calls (Dict[str, str]): Dictionary specifying the endpoints used by the entity.
            Expected keys:
            - get_all
            - get_user
            - get_instance
            - upload_instance
            - edit_instance [optional]
        all_ents (List[Union[str, Dict]]): List of ids or configurations to init storage. Should be returned by the
            `all` endpoint.
        user_ents (List[Union[str, Dict]]): List of ids or configurations that should be returned by the user endpoint.
            Non-updatable.
    Returns:
        TestStorage: A link to the storage. Whenever new entity is uploaded / edited, it is updated
    """
    get_all = comms_calls["get_all"]
    get_user = comms_calls["get_user"]
    get_instance = comms_calls["get_instance"]
    upload_instance = comms_calls["upload_instance"]

    def _to_dict_entity(ent: Union[str, Dict]) -> Tuple[str, Dict]:
        """returns pair (id, entity-as-a-full-dict)"""
        if isinstance(ent, dict):
            id_, ent_params = ent["id"], ent
        else:
            id_, ent_params = ent, {"id": ent}
        return id_, generate_fn(**ent_params).dict()

    all_ents = dict(_to_dict_entity(ent) for ent in all_ents)
    user_ents = dict(_to_dict_entity(ent) for ent in user_ents)

    storage = TestEntityStorage(generate_fn, all_ents)
    mocker.patch.object(comms, get_all, return_value=list(all_ents.values()))
    mocker.patch.object(comms, get_user, return_value=list(user_ents.values()))

    mocker.patch.object(comms, get_instance, side_effect=storage.get)
    mocker.patch.object(comms, upload_instance, side_effect=storage.upload)
    return storage
