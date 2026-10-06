import typer
from typing import Optional

import medperf.config as config
from medperf.decorators import clean_except
from medperf.entities.benchmark import Benchmark
from medperf.commands.list import EntityList
from medperf.commands.view import EntityView
from medperf.commands.benchmark.submit import SubmitBenchmark
from medperf.commands.execution.create import BenchmarkExecution
from medperf.commands.benchmark.update_associations_poilcy import (
    UpdateAssociationsPolicy,
)
from medperf.commands.benchmark.update_committee_members import UpdateCommitteeMembers
import medperf.help_texts as help_texts

app = typer.Typer()


@app.command("ls")
@clean_except
def list(
    unregistered: bool = typer.Option(
        False, "--unregistered", help=help_texts.Benchmark.ls_unregistered
    ),
    mine: bool = typer.Option(False, "--mine", help=help_texts.Benchmark.ls_mine),
    name: str = typer.Option(None, "--name", help=help_texts.Common.name_filter),
    owner: int = typer.Option(None, "--owner", help=help_texts.Common.owner_filter),
    state: str = typer.Option(None, "--state", help=help_texts.Common.state_filter),
    is_valid: bool = typer.Option(
        None, "--valid/--invalid", help=help_texts.Common.valid_filter
    ),
    is_active: bool = typer.Option(
        None, "--active/--inactive", help=help_texts.Common.active_filter
    ),
    data_prep: int = typer.Option(
        None,
        "-d",
        "--data-preparation-container",
        help=help_texts.Benchmark.data_preparation_container_filter,
    ),
):
    """List benchmarks"""
    filters = {
        "name": name,
        "owner": owner,
        "state": state,
        "is_valid": is_valid,
        "is_active": is_active,
        "data_preparation_mlcube": data_prep,
    }

    EntityList.run(
        Benchmark,
        fields=[
            "UID",
            "Name",
            "Description",
            "Data Preparation Container",
            "State",
            "Approval Status",
            "Registered",
        ],
        unregistered=unregistered,
        mine_only=mine,
        **filters,
    )


@app.command("submit")
@clean_except
def submit(
    name: str = typer.Option(..., "--name", "-n", help=help_texts.Benchmark.name),
    description: str = typer.Option(
        ..., "--description", "-d", help=help_texts.Benchmark.description
    ),
    docs_url: str = typer.Option(
        "", "--docs-url", "-u", help=help_texts.Common.docs_url
    ),
    demo_url: str = typer.Option(
        "",
        "--demo-url",
        help=help_texts.Benchmark.demo_url_cli,
    ),
    demo_hash: str = typer.Option(
        "", "--demo-hash", help=help_texts.Benchmark.demo_hash
    ),
    data_preparation_container: int = typer.Option(
        ...,
        "--data-preparation-container",
        "-p",
        help=help_texts.Benchmark.data_preparation_container,
    ),
    reference_model: int = typer.Option(
        ..., "--reference-model", "-m", help=help_texts.Benchmark.reference_model
    ),
    evaluator_container: int = typer.Option(
        ...,
        "--evaluator-container",
        "-e",
        help=help_texts.Benchmark.evaluator_container,
    ),
    skip_data_preparation_step: bool = typer.Option(
        False,
        "--skip-demo-data-preparation",
        help=help_texts.Benchmark.skip_demo_data_preparation,
    ),
    operational: bool = typer.Option(
        False,
        "--operational",
        help=help_texts.Benchmark.operational,
    ),
    skip_compatibility_tests: bool = typer.Option(
        False,
        "--skip-compatibility-tests",
        help=help_texts.Benchmark.skip_compatibility_tests,
    ),
):
    """Submits a new benchmark to the platform"""
    benchmark_info = {
        "name": name,
        "description": description,
        "docs_url": docs_url,
        "demo_dataset_tarball_url": demo_url,
        "demo_dataset_tarball_hash": demo_hash,
        "data_preparation_mlcube": data_preparation_container,
        "reference_model": reference_model,
        "data_evaluator_mlcube": evaluator_container,
        "state": "OPERATION" if operational else "DEVELOPMENT",
    }
    SubmitBenchmark.run(
        benchmark_info,
        skip_data_preparation_step=skip_data_preparation_step,
        skip_compatibility_tests=skip_compatibility_tests,
    )
    config.ui.print("✅ Done!")


@app.command("run")
@clean_except
def run(
    benchmark_uid: int = typer.Option(
        ..., "--benchmark", "-b", help=help_texts.Benchmark.uid
    ),
    data_uid: int = typer.Option(
        ..., "--data_uid", "-d", help=help_texts.Dataset.registered_uid
    ),
    file: str = typer.Option(
        None,
        "--models-from-file",
        "-f",
        help=help_texts.Benchmark.models_from_file,
    ),
    ignore_model_errors: bool = typer.Option(
        False,
        "--ignore-model-errors",
        help=help_texts.Common.ignore_model_errors,
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help=help_texts.Common.no_cache,
    ),
    rerun_finalized: bool = typer.Option(
        False,
        "--rerun-finalized",
        help=help_texts.Benchmark.rerun_finalized,
    ),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model"""
    BenchmarkExecution.run(
        benchmark_uid,
        data_uid,
        models_uids=None,
        models_input_file=file,
        ignore_model_errors=ignore_model_errors,
        no_cache=no_cache,
        show_summary=True,
        ignore_failed_experiments=True,
        rerun_finalized_executions=rerun_finalized,
    )
    config.ui.print("✅ Done!")


@app.command("view")
@clean_except
def view(
    entity_id: Optional[int] = typer.Argument(None, help=help_texts.Benchmark.id),
    format: str = typer.Option(
        "yaml",
        "-f",
        "--format",
        help=help_texts.Common.format,
    ),
    unregistered: bool = typer.Option(
        False,
        "--unregistered",
        help=help_texts.Benchmark.view_unregistered,
    ),
    mine: bool = typer.Option(
        False,
        "--mine",
        help=help_texts.Benchmark.view_mine,
    ),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help=help_texts.Common.output,
    ),
):
    """Displays the information of one or more benchmarks"""
    EntityView.run(entity_id, Benchmark, format, unregistered, mine, output)


@app.command("update_associations_policy")
@clean_except
def update_associations_policy(
    benchmark_uid: int = typer.Option(
        ..., "--benchmark", "-b", help=help_texts.Benchmark.uid
    ),
    dataset_auto_approve_mode: str = typer.Option(
        None,
        "--dataset_auto_approve_mode",
        help=help_texts.Benchmark.dataset_auto_approve_mode,
    ),
    dataset_auto_approve_file: str = typer.Option(
        None,
        "--dataset_auto_approve_file",
        help=help_texts.Benchmark.dataset_auto_approve_file,
    ),
    model_auto_approve_mode: str = typer.Option(
        None,
        "--model_auto_approve_mode",
        help=help_texts.Benchmark.model_auto_approve_mode,
    ),
    model_auto_approve_file: str = typer.Option(
        None,
        "--model_auto_approve_file",
        help=help_texts.Benchmark.model_auto_approve_file,
    ),
):
    """Updates the auto-approval policy of dataset and model associations of a benchmark"""
    UpdateAssociationsPolicy.run(
        benchmark_uid,
        dataset_mode=dataset_auto_approve_mode,
        dataset_emails_file=dataset_auto_approve_file,
        model_mode=model_auto_approve_mode,
        model_emails_file=model_auto_approve_file,
    )


@app.command("update_committee_members")
@clean_except
def update_committee_members(
    benchmark_uid: int = typer.Option(
        ..., "--benchmark", "-b", help=help_texts.Benchmark.uid
    ),
    committee_emails_file: str = typer.Option(
        None,
        "--committee_emails_file",
        help=help_texts.Benchmark.committee_emails_file,
    ),
    committee_emails: str = typer.Option(
        None,
        "--committee_emails",
        help=help_texts.Benchmark.committee_emails,
    ),
):
    """Updates the committee members for a benchmark"""
    UpdateCommitteeMembers.run(
        benchmark_uid,
        committee_emails_file=committee_emails_file,
        committee_emails=committee_emails,
    )
