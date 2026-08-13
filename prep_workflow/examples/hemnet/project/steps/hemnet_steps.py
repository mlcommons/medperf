"""HEMnet histopathology preparation, ported to the in-container engine.

The reused HEMnet scripts are invoked as subprocesses (exactly as the reference
did), from the directory where they and their dependencies live in the image.
Per-subject scripts receive ``-s <slide-prefix>``; barrier scripts run once.
"""

import os
import subprocess

from prep_workflow import Step

SCRIPTS_DIR = os.environ.get("HEMNET_SCRIPTS", "/HEMnet/HEMnet")


def _run(script, *args):
    subprocess.run(
        ["python", os.path.join(SCRIPTS_DIR, script), *args],
        cwd=SCRIPTS_DIR,
        check=True,
    )


class DiscoverSlides(Step):
    """Barrier setup: register one subject per paired TP53/H&E slide prefix
    (ported from the reference ``slides_definition``)."""

    per_subject = False

    def run(self, ctx):
        from pathlib import Path

        slides = sorted(p.name for p in Path(ctx.paths.input_data).glob("*.svs"))
        tp53 = [s for s in slides if "TP53" in s]
        he = [s for s in slides if "HandE" in s]
        for tp53_slide, _ in zip(tp53, he):
            ctx.report.add_subject(tp53_slide[:-10])


class CreateNormalisation(Step):
    per_subject = False

    def run(self, ctx):
        _run("normaliser_step.py")


class ImageRegistration(Step):
    def run(self, ctx):
        _run("image_registration.py", "-s", ctx.subject, "-v")


class AffineRegistration(Step):
    def run(self, ctx):
        _run("affine_registration.py", "-s", ctx.subject, "-v")


class BsplineRegistration(Step):
    def run(self, ctx):
        _run("bspline_registration.py", "-s", ctx.subject, "-v")


class GenerateMasks(Step):
    def run(self, ctx):
        _run("generate_masks.py", "-s", ctx.subject, "-v")


class SaveTiles(Step):
    def run(self, ctx):
        _run("save_tiles.py", "-s", ctx.subject, "-v")


class ConsolidateMetrics(Step):
    per_subject = False

    def run(self, ctx):
        _run("consolidate_metrics.py")


class Cleanup(Step):
    per_subject = False

    def run(self, ctx):
        _run("cleanup.py")


class SanityCheck(Step):
    """First step of the `statistics` task, Invoked by (--start=sanity_check). Fail if any subject is empty."""

    per_subject = False

    def run(self, ctx):
        if not os.path.isdir(ctx.paths.output_data) or not os.listdir(
            ctx.paths.output_data
        ):
            raise RuntimeError("no tiled output was produced")


class Statistics(Step):
    """`statistics` step: record how many slides were prepared."""

    per_subject = False

    def run(self, ctx):
        import yaml

        n = (
            len([p for p in os.listdir(ctx.paths.output_data)])
            if os.path.isdir(ctx.paths.output_data)
            else 0
        )
        os.makedirs(os.path.dirname(ctx.paths.statistics_file), exist_ok=True)
        with open(ctx.paths.statistics_file, "w") as f:
            yaml.safe_dump({"num_slides": n}, f)
