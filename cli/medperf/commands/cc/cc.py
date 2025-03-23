import typer

import medperf.config as config
from medperf.decorators import clean_except
from medperf.commands.cc.encrypt import ImageEncryption, DataEncryption
from medperf.commands.cc.submit_kbs import SubmitKbs
from medperf.commands.cc.submit_as import SubmitAs
from medperf.commands.cc.run_as import RunAs
from medperf.commands.cc.run_kbs import RunKbs

app = typer.Typer()


@app.command("encrypt_and_push_image")
@clean_except
def encrypt_and_push_image(
    source_image: str = typer.Option(..., "--source_image", "-s", help="Source image to encrypt and push."),
    target: str = typer.Option(..., "--target", "-t", help="Where to push the encrypted image."),
    kbs_id: int = typer.Option(..., "--kbs", "-k", help="kbs."),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model"""
    ImageEncryption.run(source_image, target, kbs_id)
    config.ui.print("✅ Done!")


@app.command("encrypt_data")
@clean_except
def encrypt_data(
    dataset_id: int = typer.Option(..., "--dataset_id", "-d", help="Source image to encrypt and push."),
    output_folder: str = typer.Option(..., "--output_folder", "-o", help="Where to save the encrypted dataset"),
    url: str = typer.Option(..., "--url", "-u", help="Where the data will be hosted."),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model"""
    DataEncryption.run(dataset_id, output_folder, url)
    config.ui.print("✅ Done!")


@app.command("submit_kbs")
@clean_except
def submit_kbs(
    address: str = typer.Option(..., "--address", "-a", help="Source image to encrypt and push."),
    port: int = typer.Option(..., "--port", "-p", help="Where to push the encrypted image."),
    attestation_service: int = typer.Option(..., "--attestation-service", "-s", help="Attestation service to verify tokens"),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model"""
    SubmitKbs.run(address, port, attestation_service)
    config.ui.print("✅ Done!")


@app.command("submit_as")
@clean_except
def submit_as(
    address: str = typer.Option(..., "--address", "-a", help="Source image to encrypt and push."),
    port: int = typer.Option(..., "--port", "-p", help="Where to push the encrypted image."),
    kbs_port: int = typer.Option(..., "--kbs_port", "-k", help="Where to push the encrypted image."),
    rvps_port: int = typer.Option(..., "--rvps_port", "-r", help="Where to push the encrypted image."),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model"""
    SubmitAs.run(address, port, kbs_port, rvps_port)
    config.ui.print("✅ Done!")


@app.command("run_kbs")
@clean_except
def run_kbs(
    kbs_id: int = typer.Option(..., "--kbs_id", "-k", help="Attestation service to verify tokens"),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model"""
    RunKbs.run(kbs_id)
    config.ui.print("✅ Done!")


@app.command("run_as")
@clean_except
def run_as(
    as_id: int = typer.Option(..., "--as_id", "-a", help="Where to push the encrypted image."),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model"""
    RunAs.run(as_id)
    config.ui.print("✅ Done!")
