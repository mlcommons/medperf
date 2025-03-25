package policy
import rego.v1

default allow := false

allow if {{
    input["submods"]["cpu"]["ear.veraison.annotated-evidence"]["init_data"] == "{digest}"
}}