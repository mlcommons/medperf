"""MLCommons' BaaS client, vendored.

`api.py`, `universal_client.py` and `error_handling.py` are copies of
`src/baas_client/` from the `baas-client` repository, with one edit each: the
`baas_client.` imports became `baas.`. Nothing else is changed, so `diff`
against upstream is the way to update them.

Copied rather than depended on, for the reason the grader used to be copied
rather than imported: this package is the entire network surface of a workload
that runs inside an enclave, and a pip dependency is a thing that changes
without the image's digest changing.
"""
