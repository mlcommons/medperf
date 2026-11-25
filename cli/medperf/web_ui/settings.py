from fastapi import Form, APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse

from medperf import config
from medperf.commands.certificate.client_certificate import GetUserCertificate
from medperf.commands.certificate.delete_client_certificate import DeleteCertificate
from medperf.commands.certificate.submit import SubmitCertificate
from medperf.commands.certificate.utils import current_user_certificate_status
from medperf.account_management.account_management import get_medperf_user_object
from medperf.commands.utils import set_profile_args
from medperf.config_management.config_management import read_config, write_config
from medperf.commands.cc.setup_cc_operator import SetupCCOperator
from medperf.entities.ca import CA
from medperf.exceptions import InvalidArgumentError
from medperf.utils import make_pretty_dict
from medperf.init import initialize
from medperf.enums import CryptoKeyType
from medperf.web_ui.common import (
    check_user_api,
    check_user_ui,
    UITask,
    is_logged_in,
    templates,
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Slurm options editable in the settings page, in display order. The first
# ones are shown directly, the others under "Advanced Slurm options".
SLURM_FIELDS = [
    ("slurm_account", "Account"),
    ("slurm_partition", "Partition"),
    ("slurm_time", "Time Limit"),
    ("slurm_cpus_per_task", "CPUs per Task"),
    ("slurm_mem", "Memory"),
    ("slurm_gres", "Generic Resources"),
    ("slurm_extra_args", "Extra sbatch Options"),
]
SLURM_ADVANCED_FIELDS = [
    ("slurm_setup_commands", "Setup Commands"),
    ("slurm_jobs_dir", "Jobs Directory"),
    ("slurm_node_arch", "Node Architecture"),
    ("slurm_poll_interval", "Poll Interval (seconds)"),
    ("slurm_accounting_grace", "Accounting Grace (seconds)"),
]
# Integer options: optional ones are unset when empty, required ones are not
SLURM_OPTIONAL_INT_FIELDS = {"slurm_cpus_per_task"}
SLURM_REQUIRED_INT_FIELDS = {"slurm_poll_interval", "slurm_accounting_grace"}


def _parse_slurm_field(name: str, value: str):
    """Convert a Slurm option from the settings form to its profile value.
    An empty value unsets the option (the cluster's default applies)."""
    value = value.strip()
    if name in SLURM_OPTIONAL_INT_FIELDS | SLURM_REQUIRED_INT_FIELDS:
        if not value and name in SLURM_OPTIONAL_INT_FIELDS:
            return None
        if not value.isdigit() or int(value) < 1:
            raise InvalidArgumentError(f"{name} must be a positive integer")
        return int(value)
    return value or None


def _launcher_args(launcher: str, slurm_form: dict):
    """Profile settings for the launcher chosen in the settings page. The
    Slurm launcher only supports singularity, so it also sets the platform."""
    if launcher not in ("local", "slurm"):
        raise InvalidArgumentError(f"Invalid launcher: {launcher}")
    args = {"launcher": launcher}
    if launcher == "slurm":
        args["platform"] = "singularity"
    # The execution form always sends all Slurm fields, and FastAPI turns the
    # empty ones into None: those were cleared by the user.
    for name, value in slurm_form.items():
        args[name] = _parse_slurm_field(name, value or "")
    return args


@router.get("/", response_class=HTMLResponse)
def settings_ui(request: Request, current_user: bool = Depends(check_user_ui)):
    config_p = read_config()
    cas = None
    certificate_status = None
    signing_certificate_status = None

    cc_config_defaults = {}
    cc_configured = False
    cc_initialized = False

    if is_logged_in():
        cas = CA.all()
        cas = {c.id: c.name for c in cas}
        certificate_status = current_user_certificate_status(key_type=CryptoKeyType.RSA)
        signing_certificate_status = current_user_certificate_status(
            key_type=CryptoKeyType.EC
        )

        user = get_medperf_user_object()
        cc_config_defaults = user.get_cc_config()
        cc_configured = user.is_cc_configured()
        cc_initialized = user.is_cc_initialized()

    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "profiles": config_p,
            "default_gpus": config.gpus if config.gpus else "0",
            "default_platform": config.platform,
            "default_launcher": config.launcher,
            "slurm_fields": SLURM_FIELDS,
            "slurm_advanced_fields": SLURM_ADVANCED_FIELDS,
            "slurm_int_fields": SLURM_OPTIONAL_INT_FIELDS | SLURM_REQUIRED_INT_FIELDS,
            "slurm_settings": {
                name: getattr(config, name)
                for name, _ in SLURM_FIELDS + SLURM_ADVANCED_FIELDS
            },
            "cas": cas,
            "default_ca": config.certificate_authority_id,
            "default_fingerprint": config.certificate_authority_fingerprint,
            "certificate_status": certificate_status,
            "signing_certificate_status": signing_certificate_status,
            "CryptoKeyType": CryptoKeyType,
            "cc_config_defaults": cc_config_defaults,
            "cc_configured": cc_configured,
            "cc_initialized": cc_initialized,
        },
    )


@router.post("/activate_profile", response_class=JSONResponse)
def activate_profile(
    request: Request,
    profile: str = Form(...),
    current_user: bool = Depends(check_user_api),
):
    # The automatic grant access workers act as the current user; switching the
    # profile (and thus possibly the user or server) under them is not allowed.
    if request.app.state.model_auto_give_access:
        return {
            "status": "failed",
            "error": "Automatic grant access is currently running. Stop it before switching profiles.",
        }

    config_p = read_config()

    if profile not in config_p:
        return {"status": "failed", "error": "The provided profile does not exists"}

    config_p.activate(profile)
    write_config(config_p)
    initialize(for_webui=True)
    config.ui.load_history()
    return {"status": "success", "error": ""}


@router.post("/edit_profile", response_class=JSONResponse)
def edit_profile(
    gpus: str = Form(None),
    platform: str = Form(None),
    launcher: str = Form(None),
    slurm_account: str = Form(None),
    slurm_partition: str = Form(None),
    slurm_time: str = Form(None),
    slurm_cpus_per_task: str = Form(None),
    slurm_mem: str = Form(None),
    slurm_gres: str = Form(None),
    slurm_extra_args: str = Form(None),
    slurm_setup_commands: str = Form(None),
    slurm_jobs_dir: str = Form(None),
    slurm_node_arch: str = Form(None),
    slurm_poll_interval: str = Form(None),
    slurm_accounting_grace: str = Form(None),
    ca: int = Form(None),
    fingerprint: str = Form(None),
    current_user: bool = Depends(check_user_api),
):
    slurm_form = {
        "slurm_account": slurm_account,
        "slurm_partition": slurm_partition,
        "slurm_time": slurm_time,
        "slurm_cpus_per_task": slurm_cpus_per_task,
        "slurm_mem": slurm_mem,
        "slurm_gres": slurm_gres,
        "slurm_extra_args": slurm_extra_args,
        "slurm_setup_commands": slurm_setup_commands,
        "slurm_jobs_dir": slurm_jobs_dir,
        "slurm_node_arch": slurm_node_arch,
        "slurm_poll_interval": slurm_poll_interval,
        "slurm_accounting_grace": slurm_accounting_grace,
    }
    # Each settings form sends only its own fields; the others are kept.
    fields = {
        "gpus": gpus,
        "platform": platform,
        "certificate_authority_id": ca,
        "certificate_authority_fingerprint": fingerprint,
    }
    args = {name: value for name, value in fields.items() if value is not None}
    try:
        if launcher is not None:
            args.update(_launcher_args(launcher, slurm_form))
        set_profile_args(args)
        initialize(for_webui=True)
        return {"status": "success", "error": ""}
    except Exception as exp:
        logger.exception(exp)
        return {"status": "failed", "error": str(exp)}


@router.post("/view_profile", response_class=JSONResponse)
def view_profile(
    profile: str = Form(...), current_user: bool = Depends(check_user_api)
):
    return_response = {"status": "", "error": "", "profile": "", "profile_dict": ""}
    try:
        config_p = read_config()
        profile_config = config_p.active_profile
        if profile:
            if profile not in config_p:
                raise InvalidArgumentError("The provided profile does not exist")
            profile_config = config_p[profile]

        profile_config.pop(config.credentials_keyword, None)
        profile_dict = make_pretty_dict(profile_config, skip_none_values=False)

        return_response["status"] = "success"
        return_response["profile_dict"] = profile_dict
        return_response["profile"] = profile
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        logger.exception(exp)

    return return_response


@router.post("/get_certificate", response_class=JSONResponse)
def get_certificate(
    request: Request,
    key_type: CryptoKeyType = Form(...),
    current_user: bool = Depends(check_user_api),
):
    with UITask(request, "get_client_certificate") as task:
        GetUserCertificate.run(key_type=key_type)
    task.notify(
        success_message="Certificate retrieved",
        failure_message="Failed to get certificate",
    )
    return task.response


@router.post("/delete_certificate", response_class=JSONResponse)
def delete_certificate(
    request: Request,
    key_type: CryptoKeyType = Form(...),
    current_user: bool = Depends(check_user_api),
):
    with UITask(request, "delete_client_certificate") as task:
        DeleteCertificate.run(key_type=key_type)
    task.notify(
        success_message="Certificate deleted",
        failure_message="Failed to delete certificate",
    )
    return task.response


@router.post("/submit_certificate", response_class=JSONResponse)
def submit_certificate(
    request: Request,
    key_type: CryptoKeyType = Form(...),
    current_user: bool = Depends(check_user_api),
):
    with UITask(request, "submit_client_certificate") as task:
        SubmitCertificate.run(key_type=key_type)
    task.notify(
        success_message="Certificate submitted",
        failure_message="Failed to submit certificate",
    )
    return task.response


@router.post("/edit_cc_operator", response_class=JSONResponse)
def edit_cc_operator(
    configure_cc: bool = Form(False),
    project_id: str = Form(""),
    service_account_name: str = Form(""),
    bucket: str = Form(""),
    vm_zone: str = Form(""),
    vm_name: str = Form(""),
    current_user: bool = Depends(check_user_api),
):
    args = {
        "project_id": project_id,
        "service_account_name": service_account_name,
        "bucket": bucket,
        "vm_zone": vm_zone,
        "vm_name": vm_name,
    }
    if not configure_cc:
        args = {}

    try:
        SetupCCOperator.run(args)
        return {"status": "success", "error": ""}
    except Exception as exp:
        logger.exception(exp)
        return {"status": "failed", "error": str(exp)}
