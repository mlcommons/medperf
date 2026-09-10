import typer

import medperf.config as config
from medperf.decorators import clean_except
from medperf.commands.cc.dataset_configure_for_cc import DatasetConfigureForCC
from medperf.commands.cc.model_configure_for_cc import ModelConfigureForCC
from medperf.commands.cc.dataset_update_cc_policy import DatasetUpdateCCPolicy
from medperf.commands.cc.model_update_cc_policy import ModelUpdateCCPolicy
from medperf.commands.cc.setup_cc_operator import SetupCCOperator
from medperf.commands.cc.setup_cc_collector import SetupCCCollector
from medperf.commands.cc.download_cc_results import DownloadCCResults

app = typer.Typer()


@app.command("configure_dataset_for_cc")
@clean_except
def configure_dataset_for_cc(
    data_uid: int = typer.Option(..., "--data_uid", "-d", help="Dataset UID"),
    cc_config_file: str = typer.Option(
        ..., "--cc_config_file", "-c", help="path to cc config file"
    ),
    cc_policy_file: str = typer.Option(
        ..., "--cc_policy_file", "-p", help="path to cc policy file"
    ),
):
    """Configure dataset for confidential computing execution"""
    ui = config.ui
    DatasetConfigureForCC.run_from_files(data_uid, cc_config_file, cc_policy_file)
    ui.print("✅ Done!")


@app.command("configure_model_for_cc")
@clean_except
def configure_model_for_cc(
    model_uid: int = typer.Option(..., "--model_uid", "-m", help="Model UID"),
    cc_config_file: str = typer.Option(
        ..., "--cc_config_file", "-c", help="path to cc config file"
    ),
    cc_policy_file: str = typer.Option(
        ..., "--cc_policy_file", "-p", help="path to cc policy file"
    ),
):
    """Configure model for confidential computing execution"""
    ui = config.ui
    ModelConfigureForCC.run_from_files(model_uid, cc_config_file, cc_policy_file)
    ui.print("✅ Done!")


@app.command("update_dataset_cc_policy")
@clean_except
def update_dataset_cc_policy(
    data_uid: int = typer.Option(..., "--data_uid", "-d", help="Dataset UID"),
):
    """Update dataset confidential computing policy"""
    ui = config.ui
    DatasetUpdateCCPolicy.run(data_uid)
    ui.print("✅ Done!")


@app.command("update_model_cc_policy")
@clean_except
def update_model_cc_policy(
    model_uid: int = typer.Option(..., "--model_uid", "-m", help="Model UID"),
):
    """Update model confidential computing policy"""
    ui = config.ui
    ModelUpdateCCPolicy.run(model_uid)
    ui.print("✅ Done!")


@app.command("setup_cc_operator")
@clean_except
def setup_cc_operator(
    cc_config_file: str = typer.Option(
        ..., "--cc_config_file", "-c", help="path to cc config file"
    ),
):
    """Setup confidential computing operator"""
    ui = config.ui
    SetupCCOperator.run_from_files(cc_config_file)
    ui.print("✅ Done!")


@app.command("setup_cc_collector")
@clean_except
def setup_cc_collector(
    cc_config_file: str = typer.Option(
        ..., "--cc_config_file", "-c", help="path to cc config file"
    ),
):
    """Setup where you receive the results of confidential executions"""
    ui = config.ui
    SetupCCCollector.run_from_files(cc_config_file)
    ui.print("✅ Done!")


@app.command("download_cc_results")
@clean_except
def download_cc_results(
    execution_uid: int = typer.Option(
        ..., "--execution_uid", "-e", help="Execution UID"
    ),
):
    """Collect the results of a confidential execution written for you"""
    ui = config.ui
    DownloadCCResults.run(execution_uid)
    ui.print("✅ Done!")
