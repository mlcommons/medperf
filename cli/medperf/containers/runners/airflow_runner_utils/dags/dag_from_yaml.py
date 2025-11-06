from __future__ import annotations
from yaml_parser.yaml_parser import YamlParser
from airflow.sdk import DAG  # noqa: necessary for Airflow to detect DAGs in this file

parser = YamlParser()
dags = parser.build_dags()
