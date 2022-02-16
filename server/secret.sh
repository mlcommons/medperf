while getopts s:k: flag
do
    case "${flag}" in
        s) GCP_SECRET_NAME=${OPTARG};;
        k) SECRET_VAR_KEY=${OPTARG};;
    esac
done

#Extract value of a specific key from all key value pairs in gcp secret
SECRET_VAR_VALUE=$(gcloud secrets versions access latest --secret $GCP_SECRET_NAME --format "json" | jq -r .payload.data | base64 --decode | jq  --slurp --raw-input -r 'split("\n")| map({key: split("=")[0],  val: split("=")[1]}) | .[] | select(.key=='\"$SECRET_VAR_KEY\"')|.val')

echo $SECRET_VAR_VALUE
