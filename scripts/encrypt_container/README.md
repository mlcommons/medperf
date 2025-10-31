# Using GPG to encrypt a container to use with MedPerf

### ⚠️ Disclaimer

This procedure is provided **as is**, without any warranty or guarantee of accuracy, security, or fitness for a particular purpose.  
Use it at your own risk. Always review and adapt the steps according to your organization’s security policies and best practices.

## Exporting Docker image to a docker archive

```bash
docker save -o my_arhive.tar docker_image:tag
```

## Encryption using GPG

### Generate a secret

```bash
python generate_secret.py
```

This will create the file `./secret.txt` containing a 32-bytes secret, ready to be used for encryption in the next step below.

### Encrypt

```bash
gpg --batch --output my_encrypted_archive.gpg --symmetric --passphrase-file ./secret.txt ./my_arhive.tar
```

Then, make sure you host `my_encrypted_archive.gpg` somewhere public, and proceed to register this container with MedPerf.
