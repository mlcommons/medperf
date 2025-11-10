from medperf.certificates import verify_certificate_authority_by_id


def validate_profile_args(args, current_profile_args):
    __validate_ca_args(args, current_profile_args)


def __validate_ca_args(args, current_profile_args):
    id_key = "certificate_authority_id"
    fingerprint_key = "certificate_authority_fingerprint"

    id_update = id_key in args and args[id_key] != current_profile_args[id_key]
    fingerprint_update = (
        fingerprint_key in args
        and args[fingerprint_key] != current_profile_args[fingerprint_key]
    )
    # check if the fields are being updated
    if not id_update and not fingerprint_update:
        return

    target_id = args.get(id_key, current_profile_args[id_key])
    target_fingerprint = args.get(id_key, current_profile_args[fingerprint_key])

    verify_certificate_authority_by_id(target_id, target_fingerprint)
