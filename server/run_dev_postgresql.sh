# we should frequently check to ensure that the postgres version
# matches the one we use in production
# NOTE: postgresql docker images show vulnerabilities, but we are using it for dev.
#       Also the vulnerabilities don't affect how the container is primarily used.

while getopts n: flag; do
    case "${flag}" in
    n) CONTAINER_NAME=${OPTARG} ;;
    esac
done

CONTAINER_NAME="${CONTAINER_NAME:-postgreserver}"

docker run -d --name $CONTAINER_NAME \
    -p 127.0.0.1:5432:5432 \
    -e POSTGRES_USER=devuser \
    -e POSTGRES_PASSWORD=devpassword \
    -e POSTGRES_DB=devdb \
    postgres:14.10-alpine3.17
