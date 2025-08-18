from medperf.entities.ca import CA
from typing import Optional
from medperf.exceptions import InvalidArgumentError


def get_ca_from_id_model_or_training_exp(ca_id: Optional[int] = None,
                                         model_id: Optional[int] = None,
                                         training_exp_id: Optional[int] = None) -> CA:
    # This is validated in the CLI, but better keep a check here to be extra safe
    validate_exactly_one_input(ca_id=ca_id, training_exp_id=training_exp_id, model_id=model_id)
    if ca_id:
        ca = CA.get(ca_id)
    elif training_exp_id:
        ca = CA.from_experiment(training_exp_id)
    elif model_id:
        ca = CA.from_container(model_id)

    return ca


def validate_exactly_one_input(ca_id: Optional[int] = None,
                               model_id: Optional[int] = None,
                               training_exp_id: Optional[int] = None):
    """Raises exception if more than one input is provided or if no input is provided"""
    only_one_of_these = [ca_id, training_exp_id, model_id]

    if only_one_of_these.count(None) != len(only_one_of_these) - 1:
        raise InvalidArgumentError(
            "Exactly one of ca_id, training_exp_id or model_id must be provided!"
        )
