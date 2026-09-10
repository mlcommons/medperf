import os

from pydantic.datetime_parse import parse_datetime
from medperf.entities.execution import Execution
from medperf.exceptions import InvalidArgumentError
from typing import List


def read_uids_file(path: str) -> List[int]:
    """Reads a list of entity UIDs written as one comma-separated line.

    The file format both sides of a benchmark run accept: a data owner names
    models this way, a model owner names datasets.
    """
    if not os.path.exists(path):
        raise InvalidArgumentError("The given file does not exist")
    with open(path) as f:
        text = f.read()
    uids = text.strip().split(",")
    try:
        return list(map(int, uids))
    except ValueError as e:
        msg = f"Could not parse the given file: {e}. "
        msg += "The file should contain a list of comma-separated integers"
        raise InvalidArgumentError(msg)


def filter_latest_executions(executions: List[Execution]) -> List[Execution]:
    """Given a list of executions, this function
    retrieves a list containing the latest executions of each
    model-dataset-benchmark triplet.

    Args:
        executions (list[dict]): the list of executions

    Returns:
        list[dict]: the list containing the latest executions of each
                    model-dataset-benchmark triplet.
    """

    executions.sort(key=lambda exec: parse_datetime(exec.created_at))
    latest_executions = {}
    for exec in executions:
        model = exec.model
        dataset = exec.dataset
        benchmark = exec.benchmark
        latest_executions[(model, dataset, benchmark)] = exec

    return list(latest_executions.values())
