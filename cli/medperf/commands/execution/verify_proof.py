"""Checking the integrity proof attached to a benchmark result.

Answers, without trusting whoever reported the number: were these results
produced by this benchmark's script, on this dataset, with this model, inside
genuine confidential hardware?
"""

import os

import yaml

from medperf.cc.errors import as_medperf_error
from medperf.commands.execution.plan import resolve_plan
from medperf.entities.benchmark import Benchmark
from medperf.entities.dataset import Dataset
from medperf.entities.execution import Execution
from medperf.entities.model import Model
from medperf.exceptions import InvalidArgumentError
from medperf_cc.attestation import GOOGLE
from medperf_cc.proof import (
    IntegrityProof,
    ProofExpectations,
    ProofVerdict,
    verify_proof,
)

# Who MedPerf takes the word of that an attestation is genuine. Confidential
# Space tokens are signed by Google; naming the authority rather than wiring up
# what to trust is what keeps adding another one a change inside `medperf_cc`.
ATTESTATION_AUTHORITY = GOOGLE


class VerifyExecutionProof:
    """Verifies one execution's proof against what MedPerf knows it should be."""

    @classmethod
    @as_medperf_error()
    def run(cls, execution_uid: int) -> ProofVerdict:
        verifier = cls(execution_uid)
        verifier.load()
        return verifier.verify()

    def __init__(self, execution_uid: int):
        self.execution_uid = execution_uid
        self.execution = None
        self.proof = None

    def load(self):
        self.execution = Execution.get(self.execution_uid)
        self.proof = self.__read_proof()
        if self.proof is None:
            raise InvalidArgumentError(
                f"Execution {self.execution_uid} has no integrity proof."
                " Only confidential executions produce one, and only when the"
                " workload could obtain an attestation."
            )

    def verify(self) -> ProofVerdict:
        return verify_proof(
            self.proof, self.__expectations(), authority=ATTESTATION_AUTHORITY
        )

    def __read_proof(self):
        """Prefers the copy the server holds, falling back to the local one."""
        if self.execution.integrity_proof:
            return IntegrityProof.fromdict(self.execution.integrity_proof)

        local = self.execution.integrity_proof_path
        if os.path.exists(local):
            with open(local) as f:
                return IntegrityProof.fromdict(yaml.safe_load(f))
        return None

    def __expectations(self) -> ProofExpectations:
        """What MedPerf's own records say these results should be.

        Taken from the server rather than from the proof: a proof that only
        agreed with itself would establish nothing."""
        plan = resolve_plan(Benchmark.get(self.execution.benchmark))
        dataset = Dataset.get(self.execution.dataset)
        model = Model.get(self.execution.model)

        return ProofExpectations(
            script_image_hash=plan.script_hash,
            data_hash=dataset.generated_uid,
            model_hash=model.asset_obj.asset_hash,
            # These metrics came back from the server, so they have been through
            # `medperf.utils.sanitize_json` on the way up. The workload attested
            # to them as mapped by `medperf_cc.statement.json_safe`. Those two
            # mappings must agree or every metric check here fails, and it fails
            # looking like tampering rather than like the bug it is. If this
            # command starts reporting "reported metrics do not match the
            # proof", suspect them before suspecting the operator.
            results=self.execution.results,
        )
