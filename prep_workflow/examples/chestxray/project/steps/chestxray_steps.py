"""ChestXRay preparation, ported to the in-container engine.

A simple linear pipeline that reuses the tutorial's ``prepare`` / ``sanity_check``
/ ``statistics`` functions verbatim (from ``science/``). ChestXRay processes the
whole dataset at once, so every step is a barrier (``per_subject: false``).
"""

import os

import yaml

from prep_workflow import Step


def _params(ctx):
    with open(ctx.paths.parameters_file) as f:
        return yaml.safe_load(f) or {}


class Prepare(Step):
    per_subject = False

    def run(self, ctx):
        from science.prepare import prepare_dataset

        os.makedirs(ctx.paths.output_data, exist_ok=True)
        os.makedirs(ctx.paths.output_labels, exist_ok=True)
        prepare_dataset(
            ctx.paths.input_data,
            ctx.paths.input_labels,
            _params(ctx),
            ctx.paths.output_data,
            ctx.paths.output_labels,
        )


class SanityCheck(Step):
    per_subject = False

    def run(self, ctx):
        from science.sanity_check import perform_sanity_checks

        perform_sanity_checks(ctx.paths.output_data, ctx.paths.output_labels, _params(ctx))


class Statistics(Step):
    per_subject = False

    def run(self, ctx):
        from science.statistics import generate_statistics

        os.makedirs(os.path.dirname(ctx.paths.statistics_file), exist_ok=True)
        generate_statistics(
            ctx.paths.output_data,
            ctx.paths.output_labels,
            _params(ctx),
            ctx.paths.statistics_file,
        )
