from nvflare.fuel.hci.client.fl_admin_api_runner import (
    FLAdminAPIRunner,
    api_command_wrapper,
)
import os
import yaml


def main():
    username = os.environ["MEDPERF_PARTICIPANT_LABEL"]
    admin_dir = "/mlcommons/volumes/fl_workspace"
    status_file = "/mlcommons/volumes/status/status.yaml"
    runner = FLAdminAPIRunner(username=username, admin_dir=admin_dir)
    res1 = api_command_wrapper(runner.api.check_status("server"))
    res2 = api_command_wrapper(runner.api.check_status("client"))
    with open(status_file, "w") as f:
        yaml.safe_dump(
            {"client": res2["raw"]["meta"], "server": res1["raw"]["meta"]}, f
        )
    runner.api.logout()


if __name__ == "__main__":
    main()
