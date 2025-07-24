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


class ContainerTypes(Enum):
    mlcube = "mlcube"
    singularity_file = "SingularityFile"
    docker_image = "DockerImage"
    encrypted_docker_image = "EncryptedDockerImage"
    encrypted_singularity_file = "EncryptedSingularityFile"
