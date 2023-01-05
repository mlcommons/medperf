# Utility functions for mocking comms and its methods
from typing import Dict, List, Callable, Union
from unittest.mock import MagicMock
from pytest_mock.plugin import MockFixture

from medperf.exceptions import CommunicationRetrievalError


def mock_comms_entity_gets(
    mocker: MockFixture,
    comms: MagicMock,
    generate_fn: Callable,
    comms_calls: Dict[str, str],
    all_ents: List[Union[str, Dict]],
    user_ents: List[Union[str, Dict]],
    uploaded: List,
):
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
        all_ids (List[Union[str, Dict]]): List of ids or configurations that should be returned by the all endpoint
        user_ids (List[Union[str, Dict]]): List of ids or configurations that should be returned by the user endpoint
        uploaded (List): List that will be updated with uploaded instances
    """
    get_all = comms_calls["get_all"]
    get_user = comms_calls["get_user"]
    get_instance = comms_calls["get_instance"]
    upload_instance = comms_calls["upload_instance"]

    all_ents = [ent if type(ent) == dict else {"id": ent} for ent in all_ents]
    user_ents = [ent if type(ent) == dict else {"id": ent} for ent in user_ents]

    instances = [generate_fn(**ent) for ent in all_ents]
    user_instances = [generate_fn(**ent) for ent in user_ents]
    mocker.patch.object(comms, get_all, return_value=instances)
    mocker.patch.object(comms, get_user, return_value=user_instances)
    get_behavior = get_comms_instance_behavior(generate_fn, all_ents)
    mocker.patch.object(
        comms, get_instance, side_effect=get_behavior,
    )
    upload_behavior = upload_comms_instance_behavior(uploaded)
    mocker.patch.object(comms, upload_instance, side_effect=upload_behavior)


def get_comms_instance_behavior(
    generate_fn: Callable, ents: List[Union[str, Dict]]
) -> Callable:
    """Function that defines a GET behavior

    Args:
        generate_fn (Callable): Function to generate entity dictionaries
        ents (List[Union[str, Dict]]): List of Entities configurations that are allowed to return

    Return:
        function: Function that returns an entity dictionary if found,
        or raises an error if not
    """
    ids = [ent["id"] if type(ent) == dict else ent for ent in ents]

    def get_behavior(id: str):
        if id in ids:
            idx = ids.index(id)
            return generate_fn(**ents[idx])
        else:
            raise CommunicationRetrievalError

    return get_behavior


def upload_comms_instance_behavior(uploaded: List) -> Callable:
    """Function that defines the comms mocked behavior when uploading entities

    Args:
        uploaded (List): List that will be updated with uploaded entities

    Returns:
        Callable: Function containing the desired behavior
    """

    def upload_behavior(entity_dict):
        uploaded.append(entity_dict)
        return entity_dict

    return upload_behavior
