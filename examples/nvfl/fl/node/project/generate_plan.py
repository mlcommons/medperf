import json
import yaml
import os
import tarfile


def tar(filepath: str, folder: str) -> None:
    tar_arc = tarfile.open(filepath, "w:gz")
    tar_arc.add(folder, arcname=".")
    tar_arc.close()


def read_participants(project_file, aggregator_config, current_user):
    with open(project_file) as f:
        participants = yaml.safe_load(f)["participants"]
    with open(aggregator_config) as f:
        aggregator = yaml.safe_load(f)
    admin = None
    server = None
    clients = []
    for p in participants:
        if p["type"] == "client":
            clients.append(p["name"])
        elif p["type"] == "server":
            server = p["name"]
            assert server == aggregator["address"]
            assert set(aggregator["port"]) == {p["fed_learn_port"], p["admin_port"]}
        elif p["type"] == "admin":
            admin = p["name"]
            assert admin == current_user

    return admin, server, clients


def compress_kits(admin, server, clients, input_folders_base, output_folder):
    for name in [admin, server] + clients:
        filepath = os.path.join(output_folder, f"{name}.tar.gz")
        folderpath = os.path.join(input_folders_base, name)
        tar(filepath, folderpath)


def generate_mapping(admin, server, clients, mapping_file, output_metadata_file):
    dictt = {}
    dictt["admin"] = admin + ".tar.gz"
    dictt["server"] = server + ".tar.gz"
    with open(mapping_file) as f:
        mapping = yaml.safe_load(f)

    dictt["clients"] = {k: v + ".tar.gz" for k, v in mapping.items()}
    assert set(mapping.values()) == set(clients)
    with open(output_metadata_file, "w") as f:
        yaml.safe_dump(dictt, f)


def generate_plan(job_folder, job_name, plan_output_file):
    meta_file = os.path.join(job_folder, "meta.json")
    client_config = os.path.join(
        job_folder, job_name, "config", "config_fed_client.json"
    )
    server_config = os.path.join(
        job_folder, job_name, "config", "config_fed_server.json"
    )

    plan_dict = {}
    with open(meta_file) as f:
        plan_dict["meta"] = json.load(f)
    with open(client_config) as f:
        plan_dict["client_config"] = json.load(f)
    with open(server_config) as f:
        plan_dict["server_config"] = json.load(f)

    plan_dict["job_name"] = job_name

    with open(plan_output_file, "w") as f:
        yaml.safe_dump(plan_dict, f)


def main():
    project_file = "/mlcommons/volumes/training_config/secure_project.yml"
    mapping_file = "/mlcommons/volumes/training_config/mapping.yaml"
    jobs_folder = "/mlcommons/volumes/training_config/jobs"
    aggregator_config = "/mlcommons/volumes/aggregator_config"

    job_name = os.listdir(jobs_folder)[0]
    job_folder = os.path.join(jobs_folder, job_name)

    kits_base_folder = "/tmp/provision/workspace/secure_project/prod_00"
    output_kits = "/mlcommons/volumes/kits"
    kits_metadata = "/mlcommons/volumes/kits_meta/metadata.yaml"
    plan_file = "/mlcommons/volumes/plan/plan.yaml"

    current_user = os.environ["MEDPERF_PARTICIPANT_LABEL"]
    admin, server, clients = read_participants(
        project_file, aggregator_config, current_user
    )
    compress_kits(admin, server, clients, kits_base_folder, output_kits)
    generate_mapping(admin, server, clients, mapping_file, kits_metadata)
    generate_plan(job_folder, job_name, plan_file)


if __name__ == "__main__":
    main()
