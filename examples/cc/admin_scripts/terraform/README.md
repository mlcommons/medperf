# Creating the resources

Four configurations, one per cloud role. Run the ones the user needs. Someone
who is both an asset owner and an operator runs both, independently.

| directory | creates |
| --- | --- |
| `asset_owner` | KMS keyring and key, workload identity pool, bucket |
| `operator_cpu` | service account, CPU confidential VM |
| `operator_gpu` | service account, GPU confidential VM |
| `result_collector` | bucket the results are written to |

An operator runs `operator_cpu` or `operator_gpu`, not both.

Run the operator one before `result_collector`: the collector needs the
service account it creates.

## Running one

Edit `config.tf` in the directory you want. It holds everything you need to
set — names, locations, VM specs — and nothing else. Then, from Cloud Shell:

```bash
terraform init
terraform apply
terraform output -raw info
```

The last command prints what to hand to the user.

## Using something that already exists

Each `config.tf` ends with a set of `create_*` flags. Set one to `false` and
Terraform leaves that resource alone and only grants the permissions on it.
Useful when a bucket or a keyring is already there under the name you want.

## Removing

`terraform destroy` deletes only what these configurations created. It leaves
the project, the enabled APIs, and anything you set a `create_*` flag to
`false` for.

KMS keyrings and keys cannot be deleted by GCP at all, so `asset_owner`
refuses to destroy them. Remove the `prevent_destroy` blocks from its
`main.tf` if you want Terraform to forget about them.
