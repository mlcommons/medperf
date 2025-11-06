"""
This DAG is responsible for summarizing the status of the pipeline into a
yaml file that can be sent to the MedPerf stage. This summary can be used
by the Benchmark Comitte to track how Data Preparation is going at each
participant and assist users that appear to be struggling.
"""

from __future__ import annotations
import os
import yaml
import pandas as pd
import asyncio
from typing import Any, Literal
from collections import defaultdict
from medperf.containers.runners.airflow_runner_utils.api_client.client import (
    AirflowAPIClient,
)
from medperf.containers.runners.airflow_runner_utils.yaml_partial_parser import (
    YamlPartialParser,
)
from airflow.utils.state import DagRunState


class ReportSummary:

    def __init__(
        self,
        report_directory: str,
        execution_status: Literal["running", "failure", "done"],
        progress_dict: dict[str, Any] = None,
    ):
        self.report_summary_file = os.path.join(report_directory, "report_summary.yaml")
        self.execution_status = execution_status
        self.progress_dict = progress_dict if progress_dict is not None else {}

    def to_dict(self):
        report_dict = {
            "execution_status": self.execution_status,
            "progress": self.progress_dict,
        }
        return report_dict

    def write_yaml(self):
        report_dict = self.to_dict()
        with open(self.report_summary_file, "w") as f:
            yaml.dump(
                report_dict,
                f,
                sort_keys=False,
            )


class Summarizer:

    def __init__(self, yaml_parser: YamlPartialParser, report_directory: os.PathLike):
        self.step_ids = yaml_parser.step_ids
        self.report_directory = report_directory

    @staticmethod
    def _get_dag_id_to_dag_dict(client: AirflowAPIClient) -> dict[str, dict[str, Any]]:
        all_dags = client.dags.get_all_dags()["dags"]

        all_dags = {dag["dag_id"]: dag for dag in all_dags}

        return all_dags

    @staticmethod
    def _get_most_recent_dag_runs(
        all_dags: dict[str, dict[str, Any]], client: AirflowAPIClient
    ) -> dict[str, dict[str, Any] | None]:
        most_recent_dag_runs = {}

        for dag_id in all_dags.keys():
            most_recent_run = client.dag_runs.get_most_recent_dag_run(dag_id=dag_id)[
                "dag_runs"
            ]
            if not most_recent_run:
                most_recent_run = None
            else:
                most_recent_run = most_recent_run[0]
            most_recent_dag_runs[dag_id] = most_recent_run

        return most_recent_dag_runs

    def _sort_column(self, col):
        sorted_indices = []
        for task_id in col:
            if task_id in self.step_ids:
                sorted_indices.append(self.step_ids.index(task_id))
            else:
                sorted_indices.append(0)

        return sorted_indices

    def _get_report_summary(
        self,
        all_dags: dict[str, dict[str, Any]],
        most_recent_dag_runs: dict[str, dict[str, Any] | None],
    ) -> ReportSummary:

        dag_info_dicts = []
        for dag_id, run_dict in most_recent_dag_runs.items():
            this_dag = all_dags[dag_id]
            if run_dict is None:
                run_state = None
            else:
                run_state = run_dict["state"]

            dag_step_tags = [
                tag["name"] for tag in this_dag["tags"] if tag["name"] in self.step_ids
            ]
            update_dict = {
                "DAG ID": dag_id,
                "DAG Display Name": this_dag["dag_display_name"],
                "DAG Run State": run_state,
                "DAG Step Tag": dag_step_tags,
            }

            dag_info_dicts.append(update_dict)

        progress_df = pd.DataFrame(dag_info_dicts)
        progress_df = progress_df.explode("DAG Step Tag")
        progress_df = progress_df.sort_values(
            by=["DAG Step Tag"],
            key=self._sort_column,
        )
        all_dag_tags = progress_df["DAG Step Tag"].unique()
        summary_dict = defaultdict(lambda: dict())

        for dag_tag in all_dag_tags:

            relevant_df = progress_df[progress_df["DAG Step Tag"] == dag_tag]
            if relevant_df.empty:
                continue
            task_success_ratio = len(
                relevant_df[relevant_df["DAG Run State"] == DagRunState.SUCCESS]
            ) / len(relevant_df)
            success_percentage = round(task_success_ratio * 100, 3)
            summary_dict[dag_tag] = success_percentage

        summary_dict = dict(summary_dict)

        if all(
            dag_run_state == DagRunState.SUCCESS
            for dag_run_state in relevant_df["DAG Run State"]
        ):
            execution_status = "done"
        else:
            execution_status = "running"

        report_summary = ReportSummary(
            report_directory=self.report_directory,
            execution_status=execution_status,
            progress_dict=summary_dict,
        )
        return report_summary

    def summarize(
        self,
        airflow_client: AirflowAPIClient,
    ):
        all_dags = self._get_dag_id_to_dag_dict(airflow_client)
        most_recent_dag_runs = self._get_most_recent_dag_runs(all_dags, airflow_client)
        report_summary = self._get_report_summary(all_dags, most_recent_dag_runs)
        report_summary.write_yaml()

    async def summarize_every_x_seconds(
        self,
        interval_seconds: int,
        airflow_client: AirflowAPIClient,
    ):
        attempts = 1
        while True:
            attempts += 1
            self.summarize(airflow_client)
            await asyncio.sleep(interval_seconds)
