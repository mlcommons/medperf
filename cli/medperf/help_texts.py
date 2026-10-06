"""Help texts of the MedPerf CLI and web UI.

This module is the single source of truth for the help texts of CLI commands'
options and arguments. The web UI uses the same texts for its tooltips (the
module is available in the templates as `help_texts`), together with the
web-UI-only tooltips and form placeholders defined at the end of this file.

Usage:
    import medperf.help_texts as help_texts
    typer.Option(..., "--name", help=help_texts.Benchmark.name)
"""

import medperf.config as config


def _ls_unregistered(entities: str) -> str:
    return f"Get unregistered {entities}"


def _ls_mine(entities: str) -> str:
    return f"Get current-user {entities}"


def _view_unregistered(entities: str, entity: str) -> str:
    return f"Display unregistered {entities} if {entity} ID is not provided"


def _view_mine(entities: str, entity: str) -> str:
    return f"Display current-user {entities} if {entity} ID is not provided"


class Groups:
    """Help texts of the CLI command groups"""

    mlcube = "Manage containers (deprecated alias of 'container')"
    container = "Manage containers"
    result = "Manage results"
    dataset = "Manage datasets"
    benchmark = "Manage benchmarks"
    association = "Manage associations"
    profile = "Manage profiles"
    test = "Manage compatibility tests"
    auth = "Authentication"
    storage = "Storage management"
    training = "Manage training experiments"
    aggregator = "Manage aggregators"
    ca = "Manage CAs"
    certificate = "Manage certificates"
    asset = "Manage assets"
    model = "Manage models"
    confidential = "Manage confidential computing"
    web_ui = "Local web UI to manage MedPerf entities"


class Common:
    """Help texts shared by many commands"""

    format = "Format to display contents. Available formats: [yaml, json]"
    output = (
        "Output file to store contents. If not provided, the output will be displayed"
    )
    approval = "Skip approval step"
    name_filter = "Filter by name"
    owner_filter = "Filter by owner ID"
    state_filter = "Filter by state (DEVELOPMENT/OPERATION)"
    valid_filter = "Filter by valid status"
    active_filter = "Filter by active status"
    docs_url = "URL to documentation"
    no_cache = "Execute even if results already exist"
    overwrite = "Overwrite outputs if present"
    ignore_model_errors = (
        "Ignore failing models, allowing for possibly submitting partial results"
    )


class GlobalOptions:
    """Help texts of the configuration options available to all commands"""

    server = "URL of a hosted MedPerf API instance"
    auth_class = "Authentication interface to use [Auth0]"
    auth_domain = "Auth0 domain name"
    auth_jwks_url = "Auth0 JSON Web Key Set URL"
    auth_idtoken_issuer = "Auth0 ID token issuer"
    auth_client_id = "Auth0 client ID"
    auth_audience = "Server's Auth0 API identifier"
    certificate = "Path to a valid SSL certificate"
    loglevel = "Logging level [debug | info | warning | error]"
    prepare_timeout = "Maximum time in seconds before interrupting prepare task"
    sanity_check_timeout = (
        "Maximum time in seconds before interrupting sanity_check task"
    )
    statistics_timeout = "Maximum time in seconds before interrupting statistics task"
    infer_timeout = "Maximum time in seconds before interrupting infer task"
    evaluate_timeout = "Maximum time in seconds before interrupting evaluate task"
    container_loglevel = (
        "Logging level for containers to be run [debug | info | warning | error]"
    )
    platform = "Platform to use for running containers [docker | singularity]"
    gpus = (
        "What GPUs to expose to containers. "
        'Accepted values are comma-separated GPU IDs (e.g. "1,2"), or "all". '
        "Containers that aren't configured to use GPUs won't be affected by this. "
        "Defaults to all available GPUs"
    )
    gpus_inline = """
        What GPUs to expose to containers.
        Accepted values are:\n
        - "" or 0: to expose no GPUs (e.g. --gpus="")\n
        - "all": to expose all GPUs (e.g. --gpus=all)\n
        - an integer: to expose a certain number of GPUs. ONLY AVAILABLE FOR DOCKER
        (e.g. --gpus=2 to expose 2 GPUs)\n
        - Form "device=<id1>,<id2>": to expose specific GPUs
        (e.g. --gpus="device=0,2")\n"""
    shm_size = """
        Only for Docker. See the --shm-size argument
        of docker run: https://docs.docker.com/engine/containers/run/"""
    cleanup = "Whether to clean up temporary MedPerf storage after execution"
    certificate_authority_id = "Certificate Authority ID to configure the client with"
    certificate_authority_fingerprint = (
        "Expected fingerprint of the configured certificate authority"
    )


class Benchmark:
    uid = "UID of the desired benchmark"
    id = "Benchmark ID"
    # ls
    ls_unregistered = _ls_unregistered("benchmarks")
    ls_mine = _ls_mine("benchmarks")
    data_preparation_container_filter = "Filter by data preparation container UID"
    # submit
    name = "Name of the benchmark"
    description = "Description of the benchmark"
    demo_url = "Identifier to download the demonstration dataset tarball file"
    demo_url_cli = (
        f"{demo_url}.\n\n"
        "See `medperf container submit --help` for the supported identifier formats"
    )
    demo_hash = "Hash of the demonstration dataset tarball file"
    data_preparation_container = "Data preparation container UID"
    reference_model = "Reference model UID"
    evaluator_container = "Evaluator container UID"
    skip_demo_data_preparation = "Use this flag if the demo dataset is already prepared"
    operational = "Submit the benchmark as OPERATIONAL"
    skip_compatibility_tests = "Skip compatibility tests during benchmark submission"
    # run
    models_from_file = (
        "A file containing the model UIDs to be executed.\n\n"
        "The file should contain a single line as a list of "
        "comma-separated integers corresponding to the model UIDs"
    )
    rerun_finalized = (
        "Execute even if results have been already uploaded "
        "(this will create new records)"
    )
    # view
    view_unregistered = _view_unregistered("benchmarks", "benchmark")
    view_mine = _view_mine("benchmarks", "benchmark")
    # update_associations_policy
    dataset_auto_approve_mode = (
        "Can be NEVER for no auto approvals, ALWAYS for auto approving any dataset "
        "association, and ALLOWLIST for approving dataset associations with owners "
        "contained in the file given by --dataset_auto_approve_file"
    )
    dataset_auto_approve_file = (
        "File containing a list of emails of the data owners whose dataset "
        "associations will be approved when the auto approve mode is ALLOWLIST"
    )
    model_auto_approve_mode = (
        "Can be NEVER for no auto approvals, ALWAYS for auto approving any model "
        "association, and ALLOWLIST for approving model associations with owners "
        "contained in the file given by --model_auto_approve_file"
    )
    model_auto_approve_file = (
        "File containing a list of emails of the model owners whose model "
        "associations will be approved when the auto approve mode is ALLOWLIST"
    )
    # update_committee_members
    committee_emails_file = "File containing a list of committee member emails"
    committee_emails = "Space-separated list of committee member emails"


class Dataset:
    uid = "Dataset UID"
    registered_uid = "Registered dataset UID"
    id = "Dataset ID"
    # ls
    ls_unregistered = _ls_unregistered("datasets")
    ls_mine = _ls_mine("datasets")
    data_preparation_container_filter = "Filter by data preparation container UID"
    # submit
    benchmark_uid = "UID of the benchmark the dataset will be prepared for"
    data_preparation_container = "Data preparation container UID"
    data_path = "Path to the data"
    labels_path = "Path to the labels"
    metadata_path = (
        "Metadata folder location (might be required if the dataset is already "
        "prepared)"
    )
    name = "A human-readable name of the dataset"
    description = "A description of the dataset"
    location = "Location or institution the data belongs to"
    submit_as_prepared = "Use this flag if the dataset is already prepared"
    # prepare
    prepare_approval = (
        "Skip report submission approval step (in this case, it is assumed to be "
        "approved)"
    )
    # set_operational
    set_operational_approval = (
        "Skip confirmation and statistics submission approval step"
    )
    # associate
    associate_no_cache = (
        "Execute the benchmark association test even if results already exist"
    )
    # train
    restart_on_failure = (
        "Keep restarting failing training processes until keyboard interrupt"
    )
    skip_restart_on_failure_prompt = "Skip restart on failure prompt"
    # view
    view_unregistered = _view_unregistered("datasets", "dataset")
    view_mine = _view_mine("datasets", "dataset")
    # import
    import_uid = "Dataset UID to be imported"
    import_input_path = "Path of the tar.gz file (dataset backup) to be imported"
    import_raw_path = (
        "New path where the raw data of the DEVELOPMENT dataset will be saved. "
        "The directory should be empty or not exist"
    )
    # export
    export_uid = "Dataset UID to be exported"
    export_output_path = (
        "Path of the folder that will contain the tar.gz dataset backup"
    )


class Access:
    """Help texts of the access management commands of private models/containers"""

    model_id = "Private model for which access will be granted"
    benchmark_id = (
        "Benchmark UID to which the private model is associated. All data owners "
        "registered to this benchmark that have a valid certificate will be "
        "granted access to the model"
    )
    allowed_emails = (
        "Emails to restrict the data owners who will be granted access. If not "
        "provided, all eligible data owners of the benchmark are granted access"
    )
    allowed_emails_cli = f"{allowed_emails}. Separate the emails with spaces"
    interval = (
        "Time in minutes to check for updates. Minimum 5 minutes, maximum 60 "
        "minutes (an hour). Defaults to 5 minutes if not provided"
    )
    key_id = "ID of the key to delete"


class Container:
    id = "Container ID"
    # run_test
    run_test_config = "Path to the container config file"
    run_test_task = "Container task to run"
    run_test_parameters_file = "Path to the container parameters file"
    run_test_additional_files = "Path to the container additional files"
    run_test_output_logs = "File path where the container stdout will be stored"
    run_test_timeout = "Maximum time in seconds before interrupting the task"
    run_test_mounts = (
        "Comma-separated list of key=value pairs, mapping the container task "
        "inputs/outputs names to local paths"
    )
    run_test_env = (
        "Comma-separated list of key=value pairs of environment variables to "
        "pass to the container"
    )
    run_test_ports = "Comma-separated list of ports to expose"
    run_test_allow_network = "Allow the container to access the network"
    run_test_download = "Whether to pull the docker image"
    # ls
    ls_unregistered = _ls_unregistered("containers")
    ls_mine = _ls_mine("containers")
    name_filter = "Filter by container name"
    # create
    template = (
        f"Container type. Available types: [{' | '.join(config.templates.keys())}]"
    )
    image_name = "Image name"
    folder_name = "Folder name of the container files template to be created"
    output_path = "Save the generated template to the specified path"
    # submit
    name = "Name of the container"
    config_file = "Path to the container config file"
    parameters_file = "Path to the container parameters file"
    additional_file = "Identifier to download the additional files tarball"
    additional_file_cli = f"{additional_file}. See the description above"
    additional_hash = "Hash of the additional files tarball"
    image_hash = "Hash of the image file"
    operational = "Submit the container as OPERATIONAL"
    decryption_key = (
        "Path to the decryption key file for the encrypted container. The key "
        "will stay local. This should only be provided for encrypted container "
        "submissions"
    )
    # view
    view_unregistered = _view_unregistered("containers", "container")
    view_mine = _view_mine("containers", "container")
    # delete_keys / check_access
    delete_keys_id = "ID of the container whose keys will be deleted"
    check_access_id = "ID of the container to check your access to"


class Asset:
    id = "Asset ID"
    # web UI registration
    name = "Name of the asset"
    path = "Local path to the asset file"
    url = "URL to download the asset from"
    # ls
    ls_unregistered = _ls_unregistered("assets")
    ls_mine = _ls_mine("assets")
    name_filter = "Filter by asset name"
    # view
    view_unregistered = _view_unregistered("assets", "asset")
    view_mine = _view_mine("assets", "asset")


class Model:
    uid = "Model UID"
    id = "Model ID"
    # submit
    name = "Name of the model"
    operational = "Submit the model as OPERATIONAL"
    additional_file_cli = (
        f"{Container.additional_file}. "
        "See `medperf container submit --help` for the supported identifier formats"
    )
    asset_path = Asset.path
    asset_url = Asset.url
    # ls
    ls_unregistered = _ls_unregistered("models")
    ls_mine = _ls_mine("models")
    # view
    view_unregistered = _view_unregistered("models", "model")
    view_mine = _view_mine("models", "model")
    # associate
    associate_no_cache = (
        "Execute the association compatibility test even if results already exist"
    )
    # delete_keys / check_access
    delete_keys_id = "ID of the model whose keys will be deleted"
    check_access_id = "ID of the model to check your access to"


class Result:
    uid = "UID of the result"
    id = "Result ID"
    model_uid = "UID of the model to execute"
    new_result = (
        "Rerun the execution even if its result was already uploaded. "
        "This will create a new result record"
    )
    # ls
    ls_unregistered = _ls_unregistered("results")
    ls_mine = _ls_mine("results")
    benchmark_filter = "Get results for a given benchmark"
    model_filter = "Get results for a given model"
    dataset_filter = "Get results for a given dataset"
    # view
    view_unregistered = _view_unregistered("results", "result")
    view_mine = _view_mine("results", "result")


class Association:
    # ls
    ls_benchmark = "List benchmark associations"
    ls_training_exp = "List training experiment associations"
    ls_dataset = "List dataset associations"
    ls_model = "List model associations"
    approval_status = "Filter by approval status (PENDING/APPROVED/REJECTED)"
    # set_priority
    priority = (
        "Priority of the model, an integer. Models with a higher priority are "
        "executed first"
    )


class Aggregator:
    id = "Aggregator ID"
    # submit
    name = "Name of the aggregator"
    address = "Hostname or IP address where the aggregator service is reachable"
    port = "Port number the aggregator listens on (1-65535)"
    admin_port = (
        "Port number the aggregator listens on to serve admin requests (1-65535)"
    )
    aggregation_container = (
        "UID of the container that implements the aggregation logic (e.g. FedAvg) "
        "used by this aggregator"
    )
    # start
    start_training_exp_id = "UID of the training experiment whose aggregator will run"
    publish_on = "Host network interface on which the aggregator will listen"
    # ls
    ls_unregistered = _ls_unregistered("aggregators")
    ls_mine = _ls_mine("aggregators")
    # view
    view_unregistered = _view_unregistered("aggregators", "aggregator")
    view_mine = _view_mine("aggregators", "aggregator")


class CA:
    id = "CA ID"
    # submit
    name = "Name of the CA"
    config_path = "Path to the configuration file (JSON) of the CA"
    ca_container = "CA container UID"
    client_container = "Container UID to be used by clients to get a certificate"
    server_container = "Container UID to be used by servers to get a certificate"
    # ls
    ls_unregistered = _ls_unregistered("CAs")
    ls_mine = _ls_mine("CAs")
    # view
    view_unregistered = _view_unregistered("CAs", "CA")
    view_mine = _view_mine("CAs", "CA")


class Certificate:
    get_key_type = "Type of certificate to get"
    submit_key_type = "Type of certificate to submit"
    delete_key_type = "Type of certificate to delete"
    check_key_type = "Type of certificate to check"
    overwrite = "Overwrite certificate and key if present"
    aggregator_id = "UID of the aggregator you wish to get a certificate for"


class CompatibilityTest:
    id = "Test report ID"
    benchmark_uid = "UID of the benchmark to test. Optional"
    data_uid = (
        "Prepared dataset UID. Used for dataset testing. Optional. "
        "Defaults to benchmark demo dataset"
    )
    data_preparation = (
        "UID or local path to the data preparation container config file. "
        "Optional. Defaults to benchmark data preparator"
    )
    model = (
        "UID or local path to the model container config file. Optional. "
        "Defaults to benchmark reference model"
    )
    evaluator = (
        "UID or local path to the evaluator container config file. Optional. "
        "Defaults to benchmark evaluator"
    )
    no_cache = "Execute the test even if results already exist"
    skip_data_preparation = (
        "Use this flag if the passed demo dataset or data path is already prepared"
    )
    model_decryption_key = (
        "Only used for compatibility tests of encrypted containers. Path to the "
        "decryption key file for the encrypted container"
    )


class Confidential:
    config_file = "Path to the confidential computing configuration file"
    policy_file = "Path to the confidential computing policy file"


class Auth:
    synapse_token = "Personal access token to login with"
    email = "The email associated with your account"


class Profile:
    name = "Name of the profile"


class Storage:
    target_path = "Target path"


class Training:
    uid = "UID of the training experiment"
    id = "Training experiment ID"
    # submit
    name = "Name of the training experiment"
    description = "Description of the training experiment"
    data_preparation_container = (
        "UID of the data preparation container used to preprocess datasets for "
        "this experiment. Must match the one used by the datasets you associate"
    )
    fl_container = (
        "UID of the federated learning (FL) container that runs the training "
        "workflow (e.g. FL rounds, aggregation)"
    )
    fl_admin_container = (
        "UID of the optional container that provides FL admin/coordinator "
        "functionality (e.g. round control, participant selection)"
    )
    operational = "Submit the training experiment as OPERATIONAL"
    aggregator = "UID of the registered aggregator to set"
    # set_plan
    config_path = "Path to the training configuration file"
    # start_event
    event_name = "Name of the training event"
    participants_list_file = (
        "Path to a YAML file containing the list of participants. If not "
        "provided, the list will be built from the approved dataset associations"
    )
    # get_experiment_status
    silent = "Don't print the experiment status"
    # update_plan
    field_name = "Name of the training plan field to update"
    value = "New value of the field"
    # cancel_event
    report_path = "Path to the event report file to submit"
    # ls
    ls_unregistered = _ls_unregistered("training experiments")
    ls_mine = _ls_mine("training experiments")
    # view
    view_unregistered = _view_unregistered("training experiments", "experiment")
    view_mine = _view_mine("training experiments", "experiment")


class Dashboard:
    benchmark_id = "Benchmark ID to inspect preparation from"
    stages_path = "Path to the stages CSV file"
    institutions_path = "Path to a CSV file containing institution-email information"
    out_path = "Location to store progress CSVs"


class WebUI:
    port = "Port to use"


class WebUITooltips:
    """Tooltips used only by the web UI (the others reuse the CLI help texts)"""

    dataset_submit_as_prepared = "Check this box if the dataset is already prepared"
    dashboard_force_update = (
        "Rebuild the dashboard using the latest data instead of cached results"
    )
    view_profile_btn = "View the configuration of the active profile"
    get_client_certificate_btn = "Get client certificate"
    submit_certificate_btn = "Submit certificate to the MedPerf server"
    invalidate_certificate_btn = "Delete certificate/mark it as invalid"
    cc_misconfigured = (
        "There is a problem with your CC configuration. Click the button again "
        "once you resolve the problem."
    )


class WebUIPlaceholders:
    """Placeholders of the web UI forms inputs"""

    # benchmarks
    benchmark_name = "Example Benchmark"
    benchmark_description = "Example Description"
    benchmark_demo_url = "https://www.example.com/reference_dataset_tarball_example.tar"
    emails_input = "Type email then hit Enter, comma, or space"
    dashboard_stages_path = "/home/user/stages.csv"
    dashboard_institutions_path = "/home/user/institutions.csv"
    # datasets
    dataset_name = "Example Dataset"
    dataset_description = "Example Description"
    dataset_location = "Example Location"
    dataset_data_path = "/home/user/data_folder/"
    dataset_labels_path = "/home/user/labels_folder/"
    dataset_export_output_path = "/home/user/output_folder/"
    dataset_import_uid = "Exported dataset ID, e.g. 1"
    dataset_import_input_path = "/home/user/1.tar.gz"
    dataset_import_raw_path = "/home/user/new_raw_data_folder_for_DEVELOPMENT_datasets/"
    # containers
    container_name = "Example Container"
    container_config_file = "/home/user/container_config_file.yaml"
    container_parameters_file = "/home/user/container_parameters_file.yaml (Optional)"
    container_additional_file = (
        "https://www.example.com/container_additional_files.tar (Optional)"
    )
    container_decryption_key = "/home/user/container_decryption_key.key"
    # assets
    asset_name = "Example Asset"
    asset_url = "https://www.example.com/asset_example.tar"
    asset_path = "/home/user/asset_example/"
    # training experiments
    training_name = "Training experiment name"
    training_description = "Short description"
    training_docs_url = "https://..."
    training_config_path = "Path to plan config (e.g. plan.yaml)"
    training_field_name = "Field name"
    training_value = "Value"
    training_event_name = "Event name"
    training_participants_list_file = "Participants list file path (optional)"
    # aggregators
    aggregator_name = "Aggregator name"
    aggregator_address = "Hostname or IP"
    aggregator_port = "Port number"
    aggregator_admin_port = "Admin port number"
    aggregator_publish_on = "127.0.0.1"
    # auth
    login_email = "name@example.com"
    security_token = "security token"
    # listings
    search = "Search by name…"
