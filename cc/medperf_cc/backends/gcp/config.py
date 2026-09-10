"""Settings the Google Cloud backends share.

Both the bucket holding an asset and the key that opens it are granted to the
same principal: one derived by a workload identity pool from an attestation.
Every GCP backend that authorizes anything needs to name that pool.
"""

from pydantic import BaseModel


class WorkloadIdentityPool(BaseModel):
    """How a workload's attestation becomes a principal IAM understands."""

    project_number: str
    wip: str
    wip_provider: str

    @property
    def full_name(self) -> str:
        return (
            f"projects/{self.project_number}/locations/global/"
            f"workloadIdentityPools/{self.wip}"
        )

    @property
    def provider_name(self) -> str:
        """The provider inside the pool, as STS names it.

        A workload federates against a provider; the pool alone is only ever an
        IAM member prefix.
        """
        return f"{self.full_name}/providers/{self.wip_provider}"

    def principal(self, identity: str) -> str:
        """The IAM member matching one workload identity."""
        return (
            f"principalSet://iam.googleapis.com/{self.full_name}/"
            f"attribute.workload_uid/{identity}"
        )

    class Config:
        # A section of a wider configuration: keys the other services need
        # are present and are not this model's business.
        extra = "ignore"
