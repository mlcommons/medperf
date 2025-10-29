from __future__ import annotations
from operator_builders.singularity_operator_builder import SingularityOperatorBuilder
from operator_builders.docker_operator_buider import DockerOperatorBuilder
from operator_builders.empty_operator_builder import EmptyOperatorBuilder
from operator_builders.manual_approval_buider import ManualApprovalBuilder
from operator_builders.operator_builder import OperatorBuilder
import os

container_builder = (
    SingularityOperatorBuilder
    if os.getenv("CONTAINER_TYPE") == "singularity"
    else DockerOperatorBuilder
)

OPERATOR_MAPPING: dict[str, OperatorBuilder] = {
    "container": container_builder,
    "dummy": EmptyOperatorBuilder,
    "manual_approval": ManualApprovalBuilder,
}


def operator_factory(type, **kwargs) -> list[OperatorBuilder]:

    return_list = []
    try:
        operator_obj = OPERATOR_MAPPING[type]
    except KeyError:
        raise TypeError(f"Tasks of type {type} are not supported!")

    return_list = operator_obj.build_operator_list(**kwargs)
    return return_list
