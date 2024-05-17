# Deploying Step

## For Production

### Configuration and secrets

#### `ca_config`

An example of this file can be found in `dev_assets/ca.json` (or [here](https://smallstep.com/docs/step-ca/configuration/#basic-configuration-options)). This contains ca configuration, and will be modified during runtime as follows:

  * `root`: will point to the path of the root ca cert after it gets downloaded and stored.
  * `crt`: will point to the path of the intermediate ca cert after it gets downloaded and stored.
  * `key`: will point to the path of the intermediate ca key after it gets downloaded and stored.
  * `db`: will contain the database configuration. (will be taken from a secret variable)
  * `authority.provisioners.0.options.x509.templateFile`: will point to the path of the OIDC provisioner cert template after it gets downloaded and stored.
  * `authority.provisioners.1.options.x509.templateFile`: will point to the path of the ACME provisioner cert template after it gets downloaded and stored.

#### Other configuration files

  * `root_ca_crt`: The root ca certificate.
  * `intermediate_ca_crt`: The intermediate ca certificate.
  * `client_x509_template`: The OIDC provisioner cert template.
  * `server_x509_template`: The ACME provisioner cert template.
  * `proxy_config`: If a proxy need to be used, this contains an Nginx server configuration.

#### Secrets

  * `intermediate_ca_key`: The intermediate ca key.
  * `intermediate_ca_password`: The password used to encrypt the intermediate ca key.
  * `db_config`: Database connection configuration.

#### Main settings file

All secrets and configurations are separately stored in GCP's secret manager. There is a main settings file `settings.json` that is also stored on the secret manager, and it is a JSON file that contains references to the other secrets/configurations.

### Deployment

  * Build

  ```sh
  docker build -t tmptag -f Dockerfile.prod .
  ```

  * tag

  ```sh
  TAG=$(docker image ls | grep tmptag | tr -s " " | awk '{$1=$1;print}' | cut -d " " -f 3)
  docker tag tmptag us-west1-docker.pkg.dev/medperf-330914/medperf-repo/medperf-ca:$TAG
  ```

  * Push

  ```sh
  docker push us-west1-docker.pkg.dev/medperf-330914/medperf-repo/medperf-ca:$TAG
  ```

  * Setup secrets and configurations
  * Edit `cloudbuild.yaml` as needed. You may change:
    * the service account that will bind to the deployed instance.
    * the port
    * the service name if planning to deploy a new service, not a new revision of the existing service.
    * SQL instance
    * ...
  * Run `gcloud builds submit --config=cloudbuild.yaml --substitutions=SHORT_SHA=$TAG`

## For Development

### Configuration and secrets

The folder `dev_assets` contains configurations and ""secrets"" described above, but for development.

### Deployment

Build using `Dockerfile.dev` (tag it say with `local/devca:0.0.0`), then run:

```sh
docker run --volume ./dev_assets:/assets -p <interface>:443:443 local/devca:0.0.0
```

Set `<interface>` as you wish (`0.0.0.0`, `127.0.0.1`, `$(hostname -I | cut -d " " -f 1)`, ...)
