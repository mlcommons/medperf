while getopts c:k:d:g:r: flag
do
    case "${flag}" in
        c) CERT_FILE=${OPTARG};;
        k) KEY_FILE=${OPTARG};;
        d) DEPLOY=${OPTARG};;
        g) CERT_GENERATE=${OPTARG};;
        r) RESET_DB=${OPTARG};;
    esac
done

CONFIG_PATH=$HOME/.medperf_config/.local_server
DEPLOY="${DEPLOY:-1}"
CERT_GENERATE="${CERT_GENERATE:-1}"
CERT_FILE="${CERT_FILE:-$CONFIG_PATH/cert.crt}"
KEY_FILE="${KEY_FILE:-$CONFIG_PATH/cert.key}"
RESET_DB="${RESET_DB:-0}"

echo $CERT_FILE
echo $KEY_FILE
echo $DEPLOY
echo $CERT_GENERATE
echo $RESET_DB
echo $CONFIG_PATH

mkdir -p $CONFIG_PATH

if [ -z "$CERT_FILE" ]
then
  echo "CERT FILE must not be empty"
  exit 1
fi

if [ -z "$KEY_FILE" ]
then
  echo "KEY FILE must not be empty"
  exit 1
fi

if [ "$CERT_GENERATE" -eq 0 ]
then
  echo "No certs are generated as CERT_GENERATE flag is disabled"
else
    echo "Certs are generated"
    openssl req -x509 -nodes -days 365 -newkey rsa:3072 -keyout $KEY_FILE -out $CERT_FILE -subj "/C=US/ST=Any/L=Any/O=MedPerf/CN=127.0.0.1" -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
fi

if [ "$RESET_DB" -eq 1 ]
then
  # Clean DB for a fresh start
  echo "Cleaning DB as RESET_DB flag is enabled"
  rm db.sqlite3
fi

if [ "$DEPLOY" -eq 0 ]
then
    echo "Server is not deployed as DEPLOY flag is disabled"
else
    echo "Deploying django server"
    python manage.py migrate
    python manage.py collectstatic --noinput
    python manage.py runserver_plus --cert-file $CERT_FILE --key-file $KEY_FILE
fi
