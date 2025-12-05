from __future__ import annotations
from yaml_parser.yaml_parser import YamlParser

# We need to import DAG so that airflow recognizes the auto-generated DAGs
from airflow.sdk import DAG  # noqa: F401

parser = YamlParser()
dags = parser.build_dags()
