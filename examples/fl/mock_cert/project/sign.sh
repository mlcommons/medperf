while getopts so: flag; do
    case "${flag}" in
    o) OUT=${OPTARG} ;;
    s) EXT="v3_server" ;;
    esac
done

EXT="${EXT:-v3_client}"

if [ -z "$OUT" ]; then
    echo "-o is required"
    exit 1
fi

if [ -z "$MEDPERF_INPUT_CN" ]; then
    echo "MEDPERF_INPUT_CN env var is required"
    exit 1
fi

mkdir -p $OUT
cp /mlcube_project/csr.conf $OUT/
cp -r /mlcube_project/ca $OUT/
CSR_CONF=$OUT/csr.conf
CA_KEY=$OUT/ca/root.key
CA_CERT=$OUT/ca/cert/root.crt

sed -i "/^commonName = /c\commonName = $MEDPERF_INPUT_CN" $CSR_CONF
sed -i "/^DNS\.1 = /c\DNS.1 = $MEDPERF_INPUT_CN" $CSR_CONF

openssl genpkey -algorithm RSA -out $OUT/key.key -pkeyopt rsa_keygen_bits:3072
openssl req -new -key $OUT/key.key -out $OUT/csr.csr -config $CSR_CONF -extensions $EXT
openssl x509 -req -in $OUT/csr.csr -CA $CA_CERT -CAkey $CA_KEY \
    -CAcreateserial -out $OUT/crt.crt -days 36500 -sha384 -extensions ${EXT}_crt -extfile $CSR_CONF
rm $OUT/csr.csr
rm -r $OUT/ca
rm -r $OUT/csr.conf
