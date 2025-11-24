from enum import Enum


class Role(Enum):
    BENCHMARK_OWNER = "BenchmarkOwner"
    DATA_OWNER = "DataOwner"
    MODEL_OWNER = "ModelOwner"
    NONE = None


class Status(Enum):
    APPROVED = "APPROVED"
    PENDING = "PENDING"
    REJECTED = "REJECTED"


class AutoApprovalMode(Enum):
    NEVER = "NEVER"
    ALWAYS = "ALWAYS"
    ALLOWLIST = "ALLOWLIST"


class ContainerConfigMountKeys(Enum):
    data_path = "data_path"
    output_path = "output_path"
    labels_path = "labels_path"
    output_labels_path = "output_labels_path"
    statistics_file = "statistics_file"
    additional_files = "additional_files"
    parameters_file = "parameters_file"
