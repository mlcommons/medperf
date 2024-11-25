from medperf.exceptions import InvalidArgumentError
from medperf import config
from pydantic.datetime_parse import parse_datetime


def validate_args(
    benchmark, training_exp, dataset, model_mlcube, aggregator, ca, approval_status
):
    training_exp = bool(training_exp)
    benchmark = bool(benchmark)
    dataset = bool(dataset)
    model_mlcube = bool(model_mlcube)
    aggregator = bool(aggregator)
    ca = bool(ca)

    if approval_status is not None:
        if approval_status.lower() not in ["pending", "approved", "rejected"]:
            raise InvalidArgumentError(
                "If provided, approval status must be one of pending, approved, or rejected"
            )
    if sum([benchmark, training_exp]) != 1:
        raise InvalidArgumentError(
            "One training experiment or a benchmark flag must be provided"
        )
    if sum([dataset, model_mlcube, aggregator, ca]) != 1:
        raise InvalidArgumentError(
            "One dataset, mlcube, aggregator, or ca flag must be provided"
        )
    if training_exp and model_mlcube:
        raise InvalidArgumentError(
            "Invalid combination of arguments. There are no associations"
            " between training experiments and models mlcubes"
        )
    if benchmark and (ca or aggregator):
        raise InvalidArgumentError(
            "Invalid combination of arguments. There are no associations"
            " between benchmarks and CAs or aggregators"
        )


def filter_latest_associations(associations, experiment_key, component_key):
    """Given a list of component-experiment associations, this function
    retrieves a list containing the latest association of each
    experiment-component instance.

    Args:
        associations (list[dict]): the list of associations
        experiment_key (str): experiment identifier field in the association
        component_key (str): component identifier field in the association

    Returns:
        list[dict]: the list containing the latest association of each
                    entity instance.
    """

    associations.sort(key=lambda assoc: parse_datetime(assoc["created_at"]))
    latest_associations = {}
    for assoc in associations:
        component_id = assoc[component_key]
        experiment_id = assoc[experiment_key]
        latest_associations[(component_id, experiment_id)] = assoc

    latest_associations = list(latest_associations.values())
    return latest_associations


def get_last_component(associations, experiment_key):
    associations.sort(key=lambda assoc: parse_datetime(assoc["created_at"]))
    experiments_component = {}
    for assoc in associations:
        experiment_id = assoc[experiment_key]
        experiments_component[experiment_id] = assoc

    experiments_component = list(experiments_component.values())
    return experiments_component


def get_associations_list(
    experiment_key: str,
    component_key: str,
    approval_status: str = None,
    experiment_id: int = None,
):
    comms_functions = {
        "training_exp": {
            "dataset": {
                "user": config.comms.get_user_training_datasets_associations,
                "experiment": config.comms.get_training_datasets_associations,
            },
            "aggregator": {
                "user": config.comms.get_user_training_aggregators_associations,
            },
            "ca": {
                "user": config.comms.get_user_training_cas_associations,
            },
        },
        "benchmark": {
            "dataset": {
                "user": config.comms.get_user_benchmarks_datasets_associations,
            },
            "model_mlcube": {
                "user": config.comms.get_user_benchmarks_models_associations,
                "experiment": config.comms.get_benchmark_models_associations,
            },
        },
    }
    if experiment_id:
        comms_func = comms_functions[experiment_key][component_key]["experiment"]
        assocs = comms_func(experiment_id)
    else:
        comms_func = comms_functions[experiment_key][component_key]["user"]
        assocs = comms_func()

    assocs = filter_latest_associations(assocs, experiment_key, component_key)
    if component_key in ["aggregator", "ca"]:
        # an experiment should only have one aggregator and/or one CA
        assocs = get_last_component(assocs, experiment_key)

    if approval_status:
        approval_status = approval_status.upper()
        assocs = [
            assoc for assoc in assocs if assoc["approval_status"] == approval_status
        ]

    return assocs
