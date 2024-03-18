import os
from schema import Schema, Optional, Regex, Use, And
from .constants import PARAMS_FILE, ADD_PATH


# leaf key values in the mlcube manifest file can be dicts with a specific structure
def parse_value(val):
    if isinstance(val, dict):
        return val["default"]
    return val


class TrackParamsFile(Schema):
    """A wrapper around the default schema whose `validate` method
    accepts a set that keeps track of found optional inputs"""

    def validate(self, data, **kwargs):
        files = kwargs.pop("files")
        files.add(PARAMS_FILE)
        return super().validate(data, **kwargs)


class TrackAdditionalFiles(Schema):
    """A wrapper around the default schema whose `validate` method
    accepts a set that keeps track of found optional inputs"""

    def validate(self, data, **kwargs):
        files = kwargs.pop("files")
        files.add(ADD_PATH)
        return super().validate(data, **kwargs)


# Setup extra inputs validators: params file and additional files

# Chain validators using Schema's `And` class
params_validator = And(
    # Transform the input using `parse_value` function
    Use(parse_value),
    # Validate literal value to be PARAMS_FILE, and track file
    TrackParamsFile(PARAMS_FILE),
    error=f'"parameters_file" to be assigned to "{PARAMS_FILE}"',
)

# Chain validators using Schema's `And` class
additional_files_validator = And(
    # Transform the input using `parse_value` function
    Use(parse_value),
    # Validate according to regex, and track file
    TrackAdditionalFiles(Regex(rf"^{ADD_PATH}{os.path.sep}")),
    error=f'Additional inputs must point to files in "{ADD_PATH}"',
)

extra_inputs = {
    Optional("parameters_file"): params_validator,
    Optional(str): additional_files_validator,
}

# Define the four supported mlcube schemas

wild_card = {Optional(str): object}

PREP_MLCUBE_TASKS = Schema(
    {
        "prepare": {
            "parameters": {
                "inputs": {"data_path": object, "labels_path": object, **extra_inputs},
                "outputs": {
                    "output_path": object,
                    "output_labels_path": object,
                    "report_file": object,
                },
            },
            **wild_card,
        },
        "sanity_check": {
            "parameters": {
                "inputs": {
                    "data_path": object,
                    "labels_path": object,
                    "report_file": object,
                    **extra_inputs,
                }
            },
            **wild_card,
        },
        "statistics": {
            "parameters": {
                "inputs": {"data_path": object, "labels_path": object, **extra_inputs},
                "outputs": {"output_path": object},
            },
            **wild_card,
        },
        **wild_card,
    },
    name="Separate Labels Data Preparation MLCube",
)


MODEL_MLCUBE_TASKS = Schema(
    {
        "infer": {
            "parameters": {
                "inputs": {"data_path": object, **extra_inputs},
                "outputs": {"output_path": object},
            },
            **wild_card,
        },
        **wild_card,
    },
    name="Model MLCube",
)

METRICS_MLCUBE_TASKS = Schema(
    {
        "evaluate": {
            "parameters": {
                "inputs": {"predictions": object, "labels": object, **extra_inputs},
                "outputs": {"output_path": object},
            },
            **wild_card,
        },
        **wild_card,
    },
    name="Metrics MLCube",
)

# Put the available schemas in a dict
schemas = {
    "data-preparator": PREP_MLCUBE_TASKS,
    "model": MODEL_MLCUBE_TASKS,
    "metrics": METRICS_MLCUBE_TASKS,
}
