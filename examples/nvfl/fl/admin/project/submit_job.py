from nvflare.fuel.hci.client.fl_admin_api_runner import (
    FLAdminAPIRunner,
    api_command_wrapper,
)
import yaml
import json
import os


def prepare_job_structure(plan_file, jobs_folder):
    with open(plan_file) as f:
        plan_dict = yaml.safe_load(f)

    job_name = plan_dict["job_name"]
    job_folder = os.path.join(jobs_folder, job_name)
    config_base = os.path.join(job_folder, job_name, "config")

    os.makedirs(job_folder, exist_ok=True)
    os.makedirs(config_base, exist_ok=True)

    meta_file = os.path.join(job_folder, "meta.json")
    client_config = os.path.join(config_base, "config_fed_client.json")
    server_config = os.path.join(config_base, "config_fed_server.json")

    with open(meta_file, "w") as f:
        json.dump(plan_dict["meta"], f)
    with open(client_config, "w") as f:
        json.dump(plan_dict["client_config"], f)
    with open(server_config, "w") as f:
        json.dump(plan_dict["server_config"], f)

    return job_folder


def main():
    username = os.environ["MEDPERF_PARTICIPANT_LABEL"]
    admin_dir = "/mlcommons/volumes/fl_workspace"
    jobs_folder = "/tmp/jobs"
    plan_file = "/mlcommons/volumes/plan/plan.yaml"
    job = prepare_job_structure(plan_file, jobs_folder)
    runner = FLAdminAPIRunner(username=username, admin_dir=admin_dir)
    api_command_wrapper(runner.api.submit_job(job))
    runner.api.logout()


if __name__ == "__main__":
    main()
