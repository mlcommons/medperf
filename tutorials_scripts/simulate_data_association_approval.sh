SERVER_URL="https://localhost:8000"
VERSION_PREFIX="/api/v0"
BENCHMARK_OWNER="testbo@example.com"
DATASET="1"
BENCHMARK="1"

LOGIN_SCRIPT="$(dirname $(dirname "$0"))/server/token_from_online_storage.py"

BENCHMARK_OWNER_TOKEN=$(python $LOGIN_SCRIPT --email $BENCHMARK_OWNER)
curl -sk -X PUT $SERVER_URL$VERSION_PREFIX/datasets/$DATASET/benchmarks/$BENCHMARK/ -d '{"approval_status": "APPROVED"}' -H 'Content-Type: application/json' -H "Authorization: Bearer $BENCHMARK_OWNER_TOKEN"
