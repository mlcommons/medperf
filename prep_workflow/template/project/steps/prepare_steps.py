"""Example data-preparation steps.

This minimal pipeline turns each subject's raw image folder into a "prepared"
folder, then validates and summarizes the result. Replace these with your own
`Step` subclasses — the engine discovers every `Step` under this package.
"""

import os
import shutil

import yaml

from prep_workflow import Step


class Convert(Step):
    """Per-subject step: copy raw files into the prepared output folder.

    Real pipelines would do actual work here (format conversion, resampling, ...).
    """

    per_subject = True

    def run(self, ctx):
        raw = os.path.join(ctx.paths.input_data, ctx.subject)
        out = os.path.join(ctx.paths.output_data, ctx.subject)
        os.makedirs(out, exist_ok=True)
        for name in os.listdir(raw):
            shutil.copy(os.path.join(raw, name), os.path.join(out, name))
        ctx.logger.info("Prepared subject %s", ctx.subject)


class Collect(Step):
    """Barrier step: runs once after every subject is prepared."""

    per_subject = False

    def run(self, ctx):
        os.makedirs(ctx.paths.output_labels, exist_ok=True)
        ctx.logger.info("All %d subjects prepared.", len(ctx.subjects))


class SanityCheck(Step):
    """First step of the `statistics` task, Invoked by (--start=sanity_check). Fail if any subject is empty."""

    per_subject = False

    def run(self, ctx):
        for subject in os.listdir(ctx.paths.output_data):
            subject_dir = os.path.join(ctx.paths.output_data, subject)
            if os.path.isdir(subject_dir) and not os.listdir(subject_dir):
                raise RuntimeError(f"prepared subject '{subject}' is empty")


class Statistics(Step):
    """Final validation `statistics` step: write statistics.yaml."""

    per_subject = False

    def run(self, ctx):
        subjects = [
            s
            for s in os.listdir(ctx.paths.output_data)
            if os.path.isdir(os.path.join(ctx.paths.output_data, s))
        ]
        stats = {"num_subjects": len(subjects)}
        stats_path = ctx.paths.statistics_file
        os.makedirs(os.path.dirname(stats_path), exist_ok=True)
        with open(stats_path, "w") as f:
            yaml.safe_dump(stats, f)
