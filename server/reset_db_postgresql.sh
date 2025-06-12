while getopts n: flag; do
    case "${flag}" in
    n) CONTAINER_NAME=${OPTARG} ;;
    esac
done

CONTAINER_NAME="${CONTAINER_NAME:-postgreserver}"

docker container stop $CONTAINER_NAME
docker container rm $CONTAINER_NAME
sh run_dev_postgresql.sh -n $CONTAINER_NAME
sleep 6
python manage.py migrate
