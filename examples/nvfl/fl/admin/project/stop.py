from nvflare.fuel.hci.client.fl_admin_api_runner import (
    FLAdminAPIRunner,
    api_command_wrapper,
)
import os
import shutil


def main():
    username = os.environ["MEDPERF_PARTICIPANT_LABEL"]
    admin_dir = "/mlcommons/volumes/fl_workspace"
    output_weights = "/mlcommons/volumes/output_weights"
    runner = FLAdminAPIRunner(username=username, admin_dir=admin_dir)
    res = api_command_wrapper(runner.api.list_jobs())
    job_id = res["details"][0]["job_id"]
    api_command_wrapper(runner.api.download_job(job_id))
    shutil.move(
        os.path.join(admin_dir, "transfer", job_id, "workspace"), output_weights
    )
    api_command_wrapper(runner.api.shutdown("client"))
    api_command_wrapper(runner.api.shutdown("server"))
    runner.api.logout()


if __name__ == "__main__":
    main()
