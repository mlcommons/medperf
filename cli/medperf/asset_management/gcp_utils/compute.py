
import logging
from google.cloud import compute_v1
import time
from colorama import Fore, Style
import medperf.config as medperf_config
from .types import GCPOperatorConfig, CCWorkloadID


# taken and adapted from
# https://docs.cloud.google.com/compute/docs/samples/compute-start-instance#compute_start_instance-python
def __wait_for_extended_operation(operation, verbose_name, timeout: int = 300):
    """
    Waits for the extended (long-running) operation to complete.

    If the operation is successful, it will return its result.
    If the operation ends with an error, an exception will be raised.
    If there were any warnings during the execution of the operation
    they will be printed to sys.stderr.

    Args:
        operation: a long-running operation you want to wait on.
        verbose_name: (optional) a more verbose name of the operation,
            used only during error and warning reporting.
        timeout: how long (in seconds) to wait for operation to finish.
            If None, wait indefinitely.

    Returns:
        Whatever the operation.result() returns.

    Raises:
        This method will raise the exception received from `operation.exception()`
        or RuntimeError if there is no exception set, but there is an `error_code`
        set for the `operation`.

        In case of an operation taking longer than `timeout` seconds to complete,
        a `concurrent.futures.TimeoutError` will be raised.
    """
    result = operation.result(timeout=timeout)

    if operation.error_code:
        logging.debug(
            f"Error during {verbose_name}: [Code: {operation.error_code}]: {operation.error_message}"
        )
        raise operation.exception() or RuntimeError(operation.error_message)

    if operation.warnings:
        logging.debug(f"Warnings during {verbose_name}:\n")
        for warning in operation.warnings:
            logging.debug(
                f"WARNING from {verbose_name} - {warning.code}: {warning.message}"
            )

    return result


def run_workload(config: GCPOperatorConfig, metadata: dict[str, str]):
    """Run workload on GCP."""
    client = compute_v1.InstancesClient()
    project_id = config.project_id
    zone = config.vm_zone
    instance_name = config.vm_name

    instance = client.get(project=project_id, zone=zone, instance=instance_name)
    has_gpu = len(instance.guest_accelerators) > 0
    if has_gpu:
        metadata["tee-install-gpu-driver"] = "true"
    metadata_items = []
    for key, value in metadata.items():
        metadata_items.append(compute_v1.Items(key=key, value=value))

    metadata_resource = compute_v1.Metadata(
        fingerprint=instance.metadata.fingerprint,
        items=metadata_items,
    )
    try:
        operation = client.set_metadata(
            project=project_id,
            zone=zone,
            instance=instance_name,
            metadata_resource=metadata_resource,
        )
        __wait_for_extended_operation(operation, "set vm metadata")
    except Exception as e:
        logging.error(f"Failed to set metadata for instance {instance_name}: {e}")
        raise

    try:
        operation = client.start(project=project_id, zone=zone, instance=instance_name)
        __wait_for_extended_operation(operation, "start vm")
    except Exception as e:
        logging.error(f"Failed to start instance {instance_name}: {e}")
        raise


def wait_for_workload_completion(
    config: GCPOperatorConfig, workload_config: CCWorkloadID
):

    client = compute_v1.InstancesClient()
    project_id = config.project_id
    zone = config.vm_zone
    instance_name = config.vm_name
    next_start = 0
    while True:
        instance = client.get(project=project_id, zone=zone, instance=instance_name)
        status = instance.status
        if status == "TERMINATED":
            return "TERMINATED"
        request = compute_v1.GetSerialPortOutputInstanceRequest(
            project=project_id,
            zone=zone,
            instance=instance_name,
            start=next_start,
        )
        output = client.get_serial_port_output(request=request)
        if output.contents:
            next_start = output.next_
            medperf_config.ui.print_subprocess_logs(
                f"{Fore.WHITE}{Style.DIM}{output.contents}{Style.RESET_ALL}"
            )
            logging.debug(output.contents)

        time.sleep(config.logs_poll_frequency)
