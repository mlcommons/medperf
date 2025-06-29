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
