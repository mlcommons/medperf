while getopts u:p:s: flag
do
    case "${flag}" in
        u) ADMIN_USERNAME=${OPTARG};;
        p) ADMIN_PASS=${OPTARG};;
        s) SERVER_URL=${OPTARG};;
    esac
done
ADMIN_USERNAME="${ADMIN_USERNAME:-admin}"
ADMIN_PASS="${ADMIN_PASS:-admin}"
SERVER_URL="${SERVER_URL:-http://127.0.0.1:8000}"

echo "Admin username: $ADMIN_USERNAME"
echo "Admin password: $ADMIN_PASS"
echo "Server URL: $SERVER_URL"

echo "CREATING USERS"
# Get Admin API token using admin credentials
ADMIN_TOKEN=$(curl -s -X POST "$SERVER_URL/auth-token/" -H  "accept: application/json" -H  "Content-Type: application/json" -d "{  \"username\": \"$ADMIN_USERNAME\",  \"password\": \"$ADMIN_PASS\"}" | jq -r '.token')

if [ $ADMIN_TOKEN = null ] || [ -z $ADMIN_TOKEN ]
then 
  echo "ADMIN_TOKEN NULL"
  exit 1
else 
  echo "Admin User Token: $ADMIN_TOKEN"
fi

# Create a new user 'testbenchmarkowner' by admin(Admin API token is used)
BENCHMARK_OWNER=$(curl -s -X POST "$SERVER_URL/users/" -H  "accept: application/json" -H  "Authorization: Token $ADMIN_TOKEN" -H  "Content-Type: application/json" -d "{  \"username\": \"testbenchmarkowner\",  \"email\": \"testbo@example.com\",  \"password\": \"test\",  \"first_name\": \"testowner\",  \"last_name\": \"benchmark\"}" | jq -r .id)

if [ $BENCHMARK_OWNER = null ]
then
  echo "BENCHMARK_OWNER NULL"
  exit 1
else
  echo "Benchmark Owner User Created(by Admin User). ID: $BENCHMARK_OWNER"
fi

# Create a new user 'testmodelowner' by admin(Admin API token is used)
MODEL_OWNER=$(curl -s -X POST "$SERVER_URL/users/" -H  "accept: application/json" -H  "Authorization: Token $ADMIN_TOKEN" -H  "Content-Type: application/json" -d "{  \"username\": \"testmodelowner\",  \"email\": \"testmo@example.com\",  \"password\": \"test\",  \"first_name\": \"testowner\",  \"last_name\": \"model\"}" | jq -r .id)

if [ $MODEL_OWNER = null ]
then
  echo "MODEL_OWNER NULL"
  exit 1
else
  echo "Model Owner User Created(by Admin User). Id: $MODEL_OWNER"
fi

# Create a new user 'testdataowner' by admin(Admin API token is used)
DATA_OWNER=$(curl -s -X POST "$SERVER_URL/users/" -H  "accept: application/json" -H  "Authorization: Token $ADMIN_TOKEN" -H  "Content-Type: application/json" -d "{  \"username\": \"testdataowner\",  \"email\": \"testdo@example.com\",  \"password\": \"test\",  \"first_name\": \"testowner\",  \"last_name\": \"data\"}" | jq -r .id)

if [ $DATA_OWNER = null ]
then
  echo "DATA_OWNER NULL"
  exit 1
else
  echo "Data Owner User Created(by Admin User). ID: $DATA_OWNER"
fi

echo "##########################BENCHMARK OWNER##########################"
# Get Benchmark Owner API token(token of testbenchmarkowner user)
BENCHMARK_OWNER_TOKEN=$(curl -s -X POST "$SERVER_URL/auth-token/" -H  "accept: application/json" -H  "Content-Type: application/json" -d "{  \"username\": \"testbenchmarkowner\",  \"password\": \"test\"}" | jq -r '.token')

if [ $BENCHMARK_OWNER_TOKEN = null ]
then
  echo "BENCHMARK_OWNER_TOKEN NULL"
  exit 1
else
  echo "Benchmark Owner Token: $BENCHMARK_OWNER_TOKEN"
fi

# Create a Data preprocessor MLCube by Benchmark Owner 
DATA_PREPROCESSOR_MLCUBE=$(curl -s -X POST "$SERVER_URL/mlcubes/" -H  "accept: application/json" -H  "Authorization: Token $BENCHMARK_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{ \"name\": \"xrv_prep\", \"git_mlcube_url\": \"https://raw.githubusercontent.com/aristizabal95/medperf-server/1a0a8c21f92c3d9a162ce5e61732eed2d0eb95cc/app/database/cubes/xrv_prep/mlcube.yaml\", \"git_parameters_url\": \"https://raw.githubusercontent.com/aristizabal95/medperf-server/1a0a8c21f92c3d9a162ce5e61732eed2d0eb95cc/app/database/cubes/xrv_prep/parameters.yaml\", \"metadata\": {}}" | jq -r '.id')

if [ $DATA_PREPROCESSOR_MLCUBE = null ]
then
  echo "DATA_PREPROCESSOR_MLCUBE NULL"
  exit 1
else
  echo "Data Preprocessor MLCube Created(by Benchmark Owner). ID: $DATA_PREPROCESSOR_MLCUBE"
fi

# Update state of the Data preprocessor MLCube to OPERATION
DATA_PREPROCESSOR_MLCUBE_STATE=$(curl -s -X PUT "$SERVER_URL/mlcubes/$DATA_PREPROCESSOR_MLCUBE/" -H  "accept: application/json" -H  "Authorization: Token $BENCHMARK_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{  \"state\": \"OPERATION\"}" | jq -r '.state')

if [ $DATA_PREPROCESSOR_MLCUBE_STATE = null ]
then
  echo "DATA_PREPROCESSOR_MLCUBE_STATE NULL"
  exit 1
else
  echo "Data Preprocessor MlCube state updated to $DATA_PREPROCESSOR_MLCUBE_STATE by Benchmark Owner"
fi

# Create a reference model executor mlcube by Benchmark Owner
REFERENCE_MODEL_EXECUTOR_MLCUBE=$(curl -s -X POST "$SERVER_URL/mlcubes/" -H  "accept: application/json" -H  "Authorization: Token $BENCHMARK_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{ \"name\": \"xrv_chex_densenet\", \"git_mlcube_url\": \"https://raw.githubusercontent.com/aristizabal95/medperf-server/1a0a8c21f92c3d9a162ce5e61732eed2d0eb95cc/app/database/cubes/xrv_chex_densenet/mlcube.yaml\", \"git_parameters_url\": \"https://raw.githubusercontent.com/aristizabal95/medperf-server/1a0a8c21f92c3d9a162ce5e61732eed2d0eb95cc/app/database/cubes/xrv_chex_densenet/parameters.yaml\", \"tarball_url\": \"https://storage.googleapis.com/medperf-storage/xrv_chex_densenet.tar.gz\", \"tarball_hash\": \"c5c408b5f9ef8b1da748e3b1f2d58b8b3eebf96e\", \"metadata\": {}}" | jq -r '.id')

if [ $REFERENCE_MODEL_EXECUTOR_MLCUBE = null ]
then
  echo "REFERENCE_MODEL_EXECUTOR_MLCUBE NULL"
  exit 1
else
  echo "Reference Model Executor MlCube Created(by Benchmark Owner). ID: $REFERENCE_MODEL_EXECUTOR_MLCUBE"
fi

# Update state of the Reference Model Executor MLCube to OPERATION
REFERENCE_MODEL_EXECUTOR_MLCUBE_STATE=$(curl -s -X PUT "$SERVER_URL/mlcubes/$REFERENCE_MODEL_EXECUTOR_MLCUBE/" -H  "accept: application/json" -H  "Authorization: Token $BENCHMARK_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{  \"state\": \"OPERATION\"}" | jq -r '.state')

if [ $REFERENCE_MODEL_EXECUTOR_MLCUBE_STATE = null ]
then
  echo "REFERENCE_MODEL_EXECUTOR_MLCUBE_STATE NULL"
  exit 1
else
  echo "Reference Model Executor MlCube state updated to $REFERENCE_MODEL_EXECUTOR_MLCUBE_STATE by Benchmark Owner"
fi

# Create a Data evalutor MLCube by Benchmark Owner 
DATA_EVALUATOR_MLCUBE=$(curl -s -X POST "$SERVER_URL/mlcubes/" -H  "accept: application/json" -H  "Authorization: Token $BENCHMARK_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{ \"name\": \"xrv_metrics\", \"git_mlcube_url\": \"https://raw.githubusercontent.com/aristizabal95/medperf-server/1a0a8c21f92c3d9a162ce5e61732eed2d0eb95cc/app/database/cubes/xrv_metrics/mlcube.yaml\", \"git_parameters_url\": \"https://raw.githubusercontent.com/aristizabal95/medperf-server/1a0a8c21f92c3d9a162ce5e61732eed2d0eb95cc/app/database/cubes/xrv_metrics/parameters.yaml\", \"metadata\": {}}" | jq -r '.id')

if [ $DATA_EVALUATOR_MLCUBE = null ]
then
  echo "DATA_EVALUATOR_MLCUBE NULL"
  exit 1
else
  echo "Data Evaluator MlCube Created(by Benchmark Owner). ID: $DATA_EVALUATOR_MLCUBE"
fi

# Update state of the Data Evaluator MLCube to OPERATION
DATA_EVALUATOR_MLCUBE_STATE=$(curl -s -X PUT "$SERVER_URL/mlcubes/$DATA_EVALUATOR_MLCUBE/" -H  "accept: application/json" -H  "Authorization: Token $BENCHMARK_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{  \"state\": \"OPERATION\"}" | jq -r '.state')

if [ $DATA_EVALUATOR_MLCUBE_STATE = null ]
then
  echo "DATA_EVALUATOR_MLCUBE_STATE NULL"
  exit 1
else
  echo "Data Evaluator MlCube state updated to $DATA_EVALUATOR_MLCUBE_STATE by Benchmark Owner"
fi

# Create a new benchmark by Benchmark owner
BENCHMARK=$(curl -s -X POST "$SERVER_URL/benchmarks/" -H  "accept: application/json" -H  "Authorization: Token $BENCHMARK_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{  \"name\": \"xrv\",  \"description\": \"benchmark-sample\",  \"docs_url\": \"string\",  \"data_preparation_mlcube\": $DATA_PREPROCESSOR_MLCUBE,  \"reference_model_mlcube\": $REFERENCE_MODEL_EXECUTOR_MLCUBE,  \"data_evaluator_mlcube\": $DATA_EVALUATOR_MLCUBE}" | jq -r '.id')

if [ $BENCHMARK = null ]
then
  echo "BENCHMARK NULL"
  exit 1
else
  echo "Benchmark Created(by Benchmark Owner). ID: $BENCHMARK"
fi

# Update the benchmark state to OPERATION
BENCHMARK_STATE=$(curl -s -X PUT "$SERVER_URL/benchmarks/$BENCHMARK/" -H  "accept: application/json" -H  "Authorization: Token $BENCHMARK_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{  \"state\": \"OPERATION\"}" | jq -r '.state')

if [ $BENCHMARK_STATE = null ]
then
  echo "BENCHMARK_STATE NULL"
  exit 1
else
  echo "Benchmark state updated to $BENCHMARK_STATE by Benchmark owner"
fi

BENCHMARK_STATUS=$(curl -s -X PUT "$SERVER_URL/benchmarks/$BENCHMARK/" -H  "accept: application/json" -H  "Authorization: Token $ADMIN_TOKEN" -H  "Content-Type: application/json" -d "{  \"approval_status\": \"APPROVED\"}"| jq -r '.approval_status')

if [ $BENCHMARK_STATUS = null ]
then
  echo "BENCHMARK_STATUS NULL"
  exit 1
else
  echo "Benchmark Id: $BENCHMARK is marked $BENCHMARK_STATUS (by Admin)"
fi

echo "##########################MODEL OWNER##########################"
# Model Owner Interaction
# Get Model Owner API token(token of testmodelowner user)
MODEL_OWNER_TOKEN=$(curl -s -X POST "$SERVER_URL/auth-token/" -H  "accept: application/json" -H  "Content-Type: application/json" -d "{  \"username\": \"testmodelowner\",  \"password\": \"test\"}" | jq -r '.token')

if [ $MODEL_OWNER_TOKEN = null ]
then
  echo "MODEL_OWNER_TOKEN NULL"
  exit 1
else
  echo "Model Owner Token: $MODEL_OWNER_TOKEN"
fi

# Create a model mlcube by Model Owner
MODEL_EXECUTOR1_MLCUBE=$(curl -s -X POST "$SERVER_URL/mlcubes/" -H  "accept: application/json" -H  "Authorization: Token $MODEL_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{ \"name\": \"xrv_resnet\", \"git_mlcube_url\": \"https://raw.githubusercontent.com/aristizabal95/medical/1474432849e071c6f42e968b6461da7129ff0282/cubes/xrv_resnet/mlcube/mlcube.yaml\", \"git_parameters_url\": \"https://raw.githubusercontent.com/aristizabal95/medical/1474432849e071c6f42e968b6461da7129ff0282/cubes/xrv_resnet/mlcube/workspace/parameters.yaml\", \"tarball_url\": \"https://storage.googleapis.com/medperf-storage/xrv_resnet.tar.gz\", \"tarball_hash\": \"e70a6c8e0931537b4b3dd8c06560f227605e9ed1\", \"metadata\": {}}" | jq -r '.id')

if [ $MODEL_EXECUTOR1_MLCUBE = null ]
then
  echo "MODEL_EXECUTOR1_MLCUBE NULL"
  exit 1
else
  echo "Model MLCube Created(by Model Owner). ID: $MODEL_EXECUTOR1_MLCUBE"
fi

# Update state of the Model MLCube to OPERATION
MODEL_EXECUTOR1_MLCUBE_STATE=$(curl -s -X PUT "$SERVER_URL/mlcubes/$MODEL_EXECUTOR1_MLCUBE/" -H  "accept: application/json" -H  "Authorization: Token $MODEL_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{  \"state\": \"OPERATION\"}" | jq -r '.state')

if [ $MODEL_EXECUTOR1_MLCUBE_STATE = null ]
then
  echo "MODEL_EXECUTOR1_MLCUBE_STATE NULL"
  exit 1
else
  echo "Model MlCube state updated to $MODEL_EXECUTOR1_MLCUBE_STATE by Model Owner"
fi


# Create another model mlcube by Model Owner
MODEL_EXECUTOR2_MLCUBE=$(curl -s -X POST "$SERVER_URL/mlcubes/" -H  "accept: application/json" -H  "Authorization: Token $MODEL_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{ \"name\": \"xrv_nih_densenet\", \"git_mlcube_url\": \"https://raw.githubusercontent.com/aristizabal95/medperf-server/1a0a8c21f92c3d9a162ce5e61732eed2d0eb95cc/app/database/cubes/xrv_nih_densenet/mlcube.yaml\", \"git_parameters_url\": \"https://raw.githubusercontent.com/aristizabal95/medperf-server/1a0a8c21f92c3d9a162ce5e61732eed2d0eb95cc/app/database/cubes/xrv_nih_densenet/parameters.yaml\", \"tarball_url\": \"https://storage.googleapis.com/medperf-storage/xrv_nih_densenet.tar.gz\", \"tarball_hash\": \"2cbba4d29292ca4eadce46070478050503cd9621\", \"metadata\": {}}" | jq -r '.id')

if [ $MODEL_EXECUTOR2_MLCUBE = null ]
then
  echo "MODEL_EXECUTOR2_MLCUBE NULL"
  exit 1
else
  echo "Model MLCube Created(by Model Owner). ID: $MODEL_EXECUTOR2_MLCUBE"
fi

# Update state of the Model MLCube to OPERATION
MODEL_EXECUTOR2_MLCUBE_STATE=$(curl -s -X PUT "$SERVER_URL/mlcubes/$MODEL_EXECUTOR2_MLCUBE/" -H  "accept: application/json" -H  "Authorization: Token $MODEL_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{  \"state\": \"OPERATION\"}" | jq -r '.state')

if [ $MODEL_EXECUTOR2_MLCUBE_STATE = null ]
then
  echo "MODEL_EXECUTOR2_MLCUBE_STATE NULL"
  exit 1
else
  echo "Model MlCube state updated to $MODEL_EXECUTOR2_MLCUBE_STATE by Model Owner"
fi

# Associate the model-executor1 mlcube to the created benchmark by model owner user
MODEL_EXECUTOR1_IN_BENCHMARK=$(curl -s -X POST "$SERVER_URL/mlcubes/benchmarks/" -H  "accept: application/json" -H  "Authorization: Token $MODEL_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{  \"model_mlcube\": $MODEL_EXECUTOR1_MLCUBE,  \"benchmark\": $BENCHMARK, \"results\": {\"key1\":\"value1\", \"key2\":\"value2\"} }")

if [ $MODEL_EXECUTOR1_IN_BENCHMARK = null ]
then
  echo "MODEL_EXECUTOR1_IN_BENCHMARK NULL"
  exit 1
else
  echo "Model MlCube Id: $MODEL_EXECUTOR1_MLCUBE associated to Benchmark Id: $BENCHMARK (by Model Owner)"
fi

# Mark the model-executor1 association with created benchmark as approved by benchmark owner
MODEL_EXECUTOR1_IN_BENCHMARK_STATUS=$(curl -s -X PUT "$SERVER_URL/mlcubes/$MODEL_EXECUTOR1_MLCUBE/benchmarks/$BENCHMARK/" -H  "accept: application/json" -H  "Authorization: Token $BENCHMARK_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{  \"approval_status\": \"APPROVED\"}" | jq -r '.approval_status')

if [ $MODEL_EXECUTOR1_IN_BENCHMARK_STATUS = null ]
then
  echo "MODEL_EXECUTOR1_IN_BENCHMARK_STATUS NULL"
  exit 1
else
  echo "Model MlCube Id: $MODEL_EXECUTOR1_MLCUBE associated to Benchmark Id: $BENCHMARK is marked $MODEL_EXECUTOR1_IN_BENCHMARK_STATUS (by Benchmark Owner)"
fi

# Associate the model-executor2 mlcube to the created benchmark by model owner user
MODEL_EXECUTOR2_IN_BENCHMARK=$(curl -s -X POST "$SERVER_URL/mlcubes/benchmarks/" -H  "accept: application/json" -H  "Authorization: Token $MODEL_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{  \"model_mlcube\": $MODEL_EXECUTOR2_MLCUBE,  \"benchmark\": $BENCHMARK, \"results\": {\"key1\":\"value1\", \"key2\":\"value2\"} }")

if [ $MODEL_EXECUTOR2_IN_BENCHMARK = null ]
then
  echo "MODEL_EXECUTOR2_IN_BENCHMARK NULL"
  exit 1
else
  echo "Model MlCube Id: $MODEL_EXECUTOR2_MLCUBE associated to Benchmark Id: $BENCHMARK (by Model Owner)"
fi

# Mark the model-executor2 association with created benchmark as approved by benchmark owner
MODEL_EXECUTOR2_IN_BENCHMARK_STATUS=$(curl -s -X PUT "$SERVER_URL/mlcubes/$MODEL_EXECUTOR2_MLCUBE/benchmarks/$BENCHMARK/" -H  "accept: application/json" -H  "Authorization: Token $BENCHMARK_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{  \"approval_status\": \"APPROVED\"}" | jq -r '.approval_status')

if [ $MODEL_EXECUTOR2_IN_BENCHMARK_STATUS = null ]
then
  echo "MODEL_EXECUTOR2_IN_BENCHMARK_STATUS NULL"
  exit 1
else
  echo "Model MlCube Id: $MODEL_EXECUTOR2_MLCUBE associated to Benchmark Id: $BENCHMARK is marked $MODEL_EXECUTOR2_IN_BENCHMARK_STATUS (by Benchmark Owner)"
fi
