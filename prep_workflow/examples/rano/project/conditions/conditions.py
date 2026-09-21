"""RANO branching conditions, ported to the ``Condition`` interface.

The logic is the reference pipeline's ``conditions.py`` (checking the reviewer's
``finalized`` directory), rewritten to read from ``ctx`` instead of a
``pipeline_state`` object. Branching now lives in ``workflow.yaml`` + these
classes rather than inside each stage's ``could_run``.
"""

import os

from prep_workflow import Condition

TUMOR_REVIEW = "tumor_extraction"
BRAIN_REVIEW = "brain_mask"
BRAIN_MASK_FILE = "brainMask_fused.nii.gz"


def _finalized_dir(ctx, review_type):
    return os.path.join(
        ctx.paths.output_data, "manual_review", review_type, ctx.subject, "finalized"
    )


class AnnotationDone(Condition):
    """True once the reviewer has placed exactly the expected tumor mask file."""

    def evaluate(self, ctx) -> bool:
        finalized = _finalized_dir(ctx, TUMOR_REVIEW)
        if not os.path.isdir(finalized):
            return False
        files = os.listdir(finalized)
        if len(files) != 1:
            return False
        expected = f"{ctx.subject.replace('/', '_')}_tumorMask_model_0.nii.gz"
        return files[0] == expected


class BrainMaskChanged(Condition):
    """True when the reviewer supplied a corrected brain mask (triggers rollback)."""

    def evaluate(self, ctx) -> bool:
        finalized = _finalized_dir(ctx, BRAIN_REVIEW)
        if not os.path.isdir(finalized):
            return False
        files = os.listdir(finalized)
        return len(files) == 1 and files[0] == BRAIN_MASK_FILE
