from medperf import config
from medperf.entities.certificate import Certificate
from medperf.utils import get_pki_assets_path, remove_path
from medperf.account_management import get_medperf_user_data
import os
import base64
import logging


def _check_and_clean_certificate_corruption(local_cert_folder):
    private_key_path = os.path.join(local_cert_folder, config.private_key_file)
    certificate_path = os.path.join(local_cert_folder, config.certificate_file)

    private_key_exists = os.path.exists(private_key_path)
    certificate_exists = os.path.exists(certificate_path)

    certificate_corrupted = not private_key_exists or not certificate_exists

    if certificate_corrupted:
        remove_path(local_cert_folder, sensitive=True)


def current_user_certificate_status():
    """Check the status of the current user certificate. Possible cases:
    - No local certificate folder and no submitted certificate
    - No local certificate folder and a submitted certificate (if the user changed machines)
    - A local certificate folder and no submitted certificate
    - A local certificate folder and a submitted certificate
        - certificates could be mismatched (also could happen if the user changed machines)
        - certificates could be fine.

    This returns a dictionary as follows:

    {
        "user_cert_object": <the user certificate object, None if not found>,
        "no_certs_found": <Boolean>,
        "should_be_submitted": <Boolean>,
        "should_be_invalidated": <Boolean>,
        "no_action_required": <Boolean>,
    }

    """

    # Get remote certificate object
    user_cert_object = Certificate.get_user_certificate()

    # Get local certificate folder
    email = get_medperf_user_data()["email"]
    local_cert_folder = get_pki_assets_path(email, config.certificate_authority_id)

    # If certificate is corrupted, delete the certificate folder
    _check_and_clean_certificate_corruption(local_cert_folder)

    # Check
    exists_locally = os.path.exists(local_cert_folder)
    submitted = user_cert_object is not None

    no_certs_found = False
    should_be_submitted = False
    should_be_invalidated = False
    no_action_required = False

    if not submitted and not exists_locally:
        logging.debug("No remote or local certificate")
        no_certs_found = True
    elif not submitted and exists_locally:
        logging.debug("local certificate to be submitted")
        should_be_submitted = True
    elif submitted and not exists_locally:
        logging.debug("remote certificate with no local one")
        should_be_invalidated = True
    else:
        if not check_matching_certificates(user_cert_object, local_cert_folder):
            logging.debug("remote and local certificates don't match")
            should_be_invalidated = True
        else:
            logging.debug("remote and local certificates match")
            no_action_required = True

    status_dict = {
        "user_cert_object": user_cert_object,
        "no_certs_found": no_certs_found,
        "should_be_submitted": should_be_submitted,
        "should_be_invalidated": should_be_invalidated,
        "no_action_required": no_action_required,
    }
    logging.debug(f"Certificate status: {status_dict}")
    return status_dict


def check_matching_certificates(user_cert_object, local_cert_folder):
    local_certificate_file = os.path.join(local_cert_folder, config.certificate_file)
    if not os.path.exists(local_certificate_file):
        logging.debug(f"No local certificate found: {local_certificate_file}")
        return False
    with open(local_certificate_file, "rb") as f:
        local_certificate_content = f.read()

    remote_certificate_content = user_cert_object.certificate_content_base64
    remote_certificate_content = base64.b64decode(remote_certificate_content)

    return local_certificate_content == remote_certificate_content


def load_user_private_key():
    email = get_medperf_user_data()["email"]
    local_cert_folder = get_pki_assets_path(email, config.certificate_authority_id)
    private_key_file = os.path.join(local_cert_folder, config.private_key_file)
    if not os.path.exists(private_key_file):
        logging.debug(f"User private key file doesn't exist: {private_key_file}")
        return
    with open(private_key_file, "rb") as f:
        content_bytes = f.read()
    return content_bytes
