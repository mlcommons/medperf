step certificate create "MedPerf Root CA" \
    ./root_ca.crt \
    ./root_ca.key \
    --template ./rsa_root_ca.tpl \
    --kty RSA \
    --not-after 175320h \
    --size 3072

step certificate create "MedPerf Intermediate CA" \
    ./intermediate_ca.crt \
    ./intermediate_ca.key \
    --ca ./root_ca.crt \
    --ca-key ./root_ca.key \
    --template ./rsa_intermediate_ca.tpl \
    --kty RSA \
    --not-after 87660h \
    --size 3072
