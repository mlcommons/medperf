from pydantic.datetime_parse import parse_datetime


def filter_latest_executions(executions):
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
