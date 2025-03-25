import typer

import medperf.config as config
from medperf.decorators import clean_except
from medperf.commands.cc.encrypt import ImageEncryption, DataEncryption
from medperf.commands.cc.submit_kbs import SubmitKbs
from medperf.commands.cc.submit_as import SubmitAs
from medperf.commands.cc.run_as import RunAs
from medperf.commands.cc.run_kbs import RunKbs
from medperf.commands.cc.update_policy import UpdatePolicy

app = typer.Typer()


@app.command("encrypt_and_push_image")
@clean_except
def encrypt_and_push_image(
    model_id: int = typer.Option(..., "--model_id", "-m", help="Source image to encrypt and push."),
    target: str = typer.Option(..., "--target", "-t", help="Where to push the encrypted image."),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model"""
    ImageEncryption.run(model_id, target)
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
    key_path: str = typer.Option(..., "--key_path", help="Source image to encrypt and push."),
    crt_path: str = typer.Option(..., "--crt_path", help="Source image to encrypt and push."),
    admin_private_key_path: str = typer.Option(..., "--admin_private_key_path", help="Source image to encrypt and push."),
    admin_public_key_path: str = typer.Option(..., "--admin_public_key_path", help="Source image to encrypt and push."),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model"""
    SubmitKbs.run(
        address,
        port,
        attestation_service,
        key_path,
        crt_path,
        admin_private_key_path,
        admin_public_key_path,
    )
    config.ui.print("✅ Done!")


@app.command("submit_attestation_service")
@clean_except
def submit_attestation_service(
    address: str = typer.Option(..., "--address", "-a", help="Source image to encrypt and push."),
    port: int = typer.Option(..., "--port", "-p", help="Where to push the encrypted image."),
    kbs_port: int = typer.Option(..., "--kbs_port", "-k", help="Where to push the encrypted image."),
    rvps_port: int = typer.Option(..., "--rvps_port", "-r", help="Where to push the encrypted image."),
    key_path: str = typer.Option(..., "--key_path", help="Source image to encrypt and push."),
    crt_path: str = typer.Option(..., "--crt_path", help="Source image to encrypt and push."),
    verification_key_path: str = typer.Option(..., "--token_verification_key_path", help="Source image to encrypt and push."),
    verification_crt_path: str = typer.Option(..., "--token_verification_crt_path", help="Source image to encrypt and push."),
    admin_private_key_path: str = typer.Option(..., "--admin_private_key_path", help="Source image to encrypt and push."),
    admin_public_key_path: str = typer.Option(..., "--admin_public_key_path", help="Source image to encrypt and push."),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model"""
    SubmitAs.run(
        address,
        port,
        kbs_port,
        rvps_port,
        key_path,
        crt_path,
        verification_key_path,
        verification_crt_path,
        admin_private_key_path,
        admin_public_key_path,
    )
    config.ui.print("✅ Done!")


@app.command("run_kbs")
@clean_except
def run_kbs(
    kbs_id: int = typer.Option(..., "--kbs_id", "-k", help="Attestation service to verify tokens"),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model"""
    RunKbs.run(kbs_id)
    config.ui.print("✅ Done!")


@app.command("run_attestation_service")
@clean_except
def run_attestation_service(
    attestation_service_id: int = typer.Option(..., "--attestation_service_id", "-a", help="Where to push the encrypted image."),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model"""
    RunAs.run(attestation_service_id)
    config.ui.print("✅ Done!")


@app.command("update_kbs_policy")
@clean_except
def update_kbs_policy(
    dataset_id: int = typer.Option(None, "--dataset_id", "-d", help="Where to push the encrypted image."),
    model_id: int = typer.Option(None, "--model_id", "-m", help="Where to push the encrypted image."),
    benchmark_id: int = typer.Option(None, "--benchmark_id", "-b", help="Where to push the encrypted image."),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model"""
    UpdatePolicy.run(dataset_id, model_id, benchmark_id)
    config.ui.print("✅ Done!")
