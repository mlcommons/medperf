# Utility functions for mocking comms and its methods
from typing import Dict, List, Callable
from unittest.mock import MagicMock
from pytest_mock.plugin import MockFixture

from medperf.exceptions import CommunicationRetrievalError


def mock_comms_entity_gets(
    mocker: MockFixture,
    comms: MagicMock,
    generate_fn: Callable,
    comms_calls: Dict[str, str],
    all_ids: List[str],
    user_ids: List[str],
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
        all_ids (List[str]): List of ids that should be returned by the all endpoint
        user_ids (List[str]): List of ids that should be returned by the user endpoint
        uploaded (List): List that will be updated with uploaded instances
    """
    get_all = comms_calls["get_all"]
    get_user = comms_calls["get_user"]
    get_instance = comms_calls["get_instance"]
    upload_instance = comms_calls["upload_instance"]

    instances = [generate_fn(id=id) for id in all_ids]
    user_instances = [generate_fn(id=id) for id in user_ids]
    mocker.patch.object(comms, get_all, return_value=instances)
    mocker.patch.object(comms, get_user, return_value=user_instances)
    get_behavior = get_comms_instance_behavior(generate_fn, all_ids)
    mocker.patch.object(
        comms, get_instance, side_effect=get_behavior,
    )
    upload_behavior = upload_comms_instance_behavior(uploaded)
    mocker.patch.object(comms, upload_instance, side_effect=upload_behavior)


def get_comms_instance_behavior(generate_fn: Callable, ids: List[str]) -> Callable:
    """Function that defines a GET behavior

    Args:
        generate_fn (Callable): Function to generate entity dictionaries
        ids (List[str]): List of IDs that are allowed to return

    Return:
        function: Function that returns an entity dictionary if found,
        or raises an error if not
    """

    def get_behavior(id: str):
        if id in ids:
            id = str(id)
            return generate_fn(id=id)
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

