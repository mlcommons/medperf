from medperf.asset_management import gcp_utils


class OperatorManager:
    def __init__(self, config: dict):
        self.operator_project_id = config["operator_project_id"]
        self.workload_service_account = config["workload_service_account"]
        self.operator_account = config["operator_account"]

    def __create_service_account(self):
        """Create service account for workload"""
        gcp_utils.create_service_account(self.workload_service_account)

    def __allow_operator_to_use_service_account(self):
        """Allow operator account to use the service account"""
        service_account_email = (
            f"{self.workload_service_account}@"
            f"{self.operator_project_id}.iam.gserviceaccount.com"
        )

        gcp_utils.add_service_account_iam_policy_binding(
            service_account_email,
            f"user:{self.operator_account}",
            "roles/iam.serviceAccountUser",
        )

    def __grant_confidential_computing_workload_user(self):
        """Grant permission to generate attestation tokens"""
        service_account_email = (
            f"{self.workload_service_account}@"
            f"{self.operator_project_id}.iam.gserviceaccount.com"
        )

        gcp_utils.add_project_iam_policy_binding(
            self.operator_project_id,
            f"serviceAccount:{service_account_email}",
            "roles/confidentialcomputing.workloadUser",
        )

    def __grant_logging_log_writer(self):
        """Grant permission to write to logs"""
        service_account_email = (
            f"{self.workload_service_account}@"
            f"{self.operator_project_id}.iam.gserviceaccount.com"
        )

        gcp_utils.add_project_iam_policy_binding(
            self.operator_project_id,
            f"serviceAccount:{service_account_email}",
            "roles/logging.logWriter",
        )

    def setup(self):
        """Set up complete operator infrastructure"""
        self.__create_service_account()
        self.__allow_operator_to_use_service_account()
        self.__grant_confidential_computing_workload_user()
        self.__grant_logging_log_writer()
