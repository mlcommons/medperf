curl -o ./attestation-token.json http://127.0.0.1:8006/aa/token\?token_type\=kbs

jq -j '.token' ./attestation-token.json >token.txt
jq -j '.tee_keypair | gsub("\\\\n"; "\n")' ./attestation-token.json >key.pem

echo $DATASET_KBS_CERT | base64 -d >./kbs-crt.pem

kbs-client --url $DATASET_KBS_URL --cert-file ./kbs-crt.pem get-resource \
    --path $DATASET_SECRET_ID \
    --tee-key-file ./key.pem \
    --attestation-token ./token.txt | base64 -d >data_secret.json

curl -o ./data.enc $(jq -j '.url' ./data_secret.json)

$(jq -j '.decryption_key' ./data_secret.json) | base64 -d >decryption_key.txt

DECRYPTED_ARCHIVE="data.tar.gz"
ENCRYPTED_FILE=./data.enc
SECRET_PATH=./decryption_key.txt
DATA_FOLDER=/dataset_files

openssl enc -d -aes-256-cbc -salt -pbkdf2 -in "$ENCRYPTED_FILE" -out "$DECRYPTED_ARCHIVE" -pass file:"$SECRET_PATH"
mkdir -p $DATA_FOLDER
tar -xzf "$DECRYPTED_ARCHIVE" -C $DATA_FOLDER
rm "$DECRYPTED_ARCHIVE"

###############################

while ! curl -O http://localhost:5505/predictions.tar.gz; do
    echo "File not available yet. Retrying in 5 seconds..."
    sleep 5
done

tar -xzf predictions.tar.gz -C /

###############################

python mlcube.py --labels $DATA_FOLDER/labels --predictions /predictions --parameters_file /mlcube_project/parameters.yaml --output_path /results.yaml

cat results.yaml
exit 0
