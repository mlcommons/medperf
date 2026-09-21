"""Steps shipped with the engine so authors don't reinvent them."""

from __future__ import annotations

import os
import time
from typing import Dict, Type

from prep_workflow.base import Context, Step


class DiscoverSubjects(Step):
    """Default first (barrier) step: register one subject per sub-directory of the
    input data. Override with your own barrier step if you need custom grouping
    (e.g. subject/timepoint). Config: ``single: true`` to treat the whole dataset
    as a single subject."""

    name = "DiscoverSubjects"
    per_subject = False

    def run(self, ctx: Context) -> None:
        input_dir = ctx.paths.input_data
        if ctx.config.get("single"):
            ctx.report.add_subject("dataset", data_path=input_dir)
            return
        subjects = []
        if os.path.isdir(input_dir):
            subjects = sorted(
                name
                for name in os.listdir(input_dir)
                if os.path.isdir(os.path.join(input_dir, name))
            )
        if not subjects:
            subjects = ["dataset"]
        for subject in subjects:
            ctx.report.add_subject(
                subject, data_path=os.path.join(input_dir, subject)
            )


class ManualApproval(Step):
    """A barrier that blocks until a confirmation marker file appears.

    Works under MedPerf's non-interactive container run: the reviewer (or a demo
    ``auto_approve.sh``) creates the marker once results look good. Config keys:
    ``marker`` (path, defaults to ``<metadata>/.approved``) and ``wait`` (poll
    seconds, default 30)."""

    name = "ManualApproval"
    per_subject = False

    def run(self, ctx: Context) -> None:
        marker = ctx.config.get("marker") or os.path.join(
            ctx.paths.metadata, ".approved"
        )
        wait = float(ctx.config.get("wait", 30))
        ctx.logger.info("Waiting for manual approval marker: %s", marker)
        while not os.path.exists(marker):
            time.sleep(wait)
        ctx.logger.info("Manual approval received.")


def builtin_steps() -> Dict[str, Type[Step]]:
    return {DiscoverSubjects.name: DiscoverSubjects, ManualApproval.name: ManualApproval}
