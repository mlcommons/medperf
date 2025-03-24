# Edit a crt configuration. You can change the following items to any you want
cat <<EOF >kbs-openssl.conf
[req]
default_bits       = 2048
default_keyfile    = localhost.key
distinguished_name = req_distinguished_name
req_extensions     = req_ext
x509_extensions    = v3_ca

[req_distinguished_name]
countryName                 = Country Name (2 letter code)
countryName_default         = CN
stateOrProvinceName         = State or Province Name (full name)
stateOrProvinceName_default = Zhejiang
localityName                = Locality Name (eg, city)
localityName_default        = Hangzhou
organizationName            = Organization Name (eg, company)
organizationName_default    = localhost
organizationalUnitName      = organizationalunit
organizationalUnitName_default = Development
commonName                  = Common Name (e.g. server FQDN or YOUR name)
commonName_default          = $3
commonName_max              = 64

[req_ext]
subjectAltName = @alt_names

[v3_ca]
subjectAltName = @alt_names

[alt_names]
IP.1   = $3
EOF

# generate the private key and self-signed cert
openssl req -x509 -nodes -days 365 \
    -newkey rsa:2048 \
    -keyout $1 \
    -out $2 \
    -config kbs-openssl.conf \
    -passin pass:

rm kbs-openssl.conf
