# Get Admin API token using admin credentials
ADMIN_TOKEN=$(curl -s -X POST "http://127.0.0.1:8000/auth-token/" -H  "accept: application/json" -H  "Content-Type: application/json" -d "{  \"username\": \"admin\",  \"password\": \"admin\"}" | jq -r '.token')

echo "Admin User Token: $ADMIN_TOKEN"

# Create a new user 'testbenchmarkowner' by admin(Admin API token is used)
BENCHMARK_OWNER=$(curl -s -X POST "http://127.0.0.1:8000/users/" -H  "accept: application/json" -H  "Authorization: Token $ADMIN_TOKEN" -H  "Content-Type: application/json" -d "{  \"username\": \"testbenchmarkowner\",  \"email\": \"testbo@example.com\",  \"password\": \"test\",  \"first_name\": \"testowner\",  \"last_name\": \"benchmark\"}" | jq -r .id)

echo "Benchmark Owner User Created(by Admin User). ID: $BENCHMARK_OWNER"

# Create a new user 'testmodelowner' by admin(Admin API token is used)
MODEL_OWNER=$(curl -s -X POST "http://127.0.0.1:8000/users/" -H  "accept: application/json" -H  "Authorization: Token $ADMIN_TOKEN" -H  "Content-Type: application/json" -d "{  \"username\": \"testmodelowner\",  \"email\": \"testmo@example.com\",  \"password\": \"test\",  \"first_name\": \"testowner\",  \"last_name\": \"model\"}" | jq -r .id)

echo "Model Owner User Created(by Admin User). Id: $MODEL_OWNER"

# Create a new user 'testdataowner' by admin(Admin API token is used)
DATA_OWNER=$(curl -s -X POST "http://127.0.0.1:8000/users/" -H  "accept: application/json" -H  "Authorization: Token $ADMIN_TOKEN" -H  "Content-Type: application/json" -d "{  \"username\": \"testdataowner\",  \"email\": \"testdo@example.com\",  \"password\": \"test\",  \"first_name\": \"testowner\",  \"last_name\": \"data\"}" | jq -r .id)

echo "Data Owner User Created(by Admin User). ID: $DATA_OWNER"

echo "##########################BENCHMARK OWNER##########################"
# Get Benchmark Owner API token(token of testbenchmarkowner user)
BENCHMARK_OWNER_TOKEN=$(curl -s -X POST "http://127.0.0.1:8000/auth-token/" -H  "accept: application/json" -H  "Content-Type: application/json" -d "{  \"username\": \"testbenchmarkowner\",  \"password\": \"test\"}" | jq -r '.token')

echo "Benchmark Owner Token: $BENCHMARK_OWNER_TOKEN"

# Create a Data preprocessor MLCube by Benchmark Owner 
DATA_PREPROCESSOR_MLCUBE=$(curl -s -X POST "http://127.0.0.1:8000/mlcubes/" -H  "accept: application/json" -H  "Authorization: Token $BENCHMARK_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{  \"name\": \"datapreprocessor\",  \"git_mlcube_url\": \"string\", \"git_parameters_url\": \"string\", \"tarball_url\": \"string\",  \"tarball_hash\": \"string\",  \"metadata\": {}}" | jq -r '.id')

echo "Data Preprocessor MLCube Created(by Benchmark Owner). ID: $DATA_PREPROCESSOR_MLCUBE"

# Create a reference model executor mlcube by Benchmark Owner
REFERENCE_MODEL_EXECUTOR_MLCUBE=$(curl -s -X POST "http://127.0.0.1:8000/mlcubes/" -H  "accept: application/json" -H  "Authorization: Token $BENCHMARK_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{  \"name\": \"reference-model\",  \"git_mlcube_url\": \"string\", \"git_parameters_url\": \"string\", \"tarball_url\": \"string\",  \"tarball_hash\": \"string\",  \"metadata\": {}}" | jq -r '.id')


echo "Reference Model Executor MlCube Created(by Benchmark Owner). ID: $REFERENCE_MODEL_EXECUTOR_MLCUBE"

# Create a Data evalutor MLCube by Benchmark Owner 
DATA_EVALUATOR_MLCUBE=$(curl -s -X POST "http://127.0.0.1:8000/mlcubes/" -H  "accept: application/json" -H  "Authorization: Token $BENCHMARK_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{  \"name\": \"evaluator\",  \"git_mlcube_url\": \"string\", \"git_parameters_url\": \"string\", \"tarball_url\": \"string\",  \"tarball_hash\": \"string\",  \"metadata\": {}}" | jq -r '.id')

echo "Data Evaluator MlCube Created(by Benchmark Owner). ID: $DATA_EVALUATOR_MLCUBE"

# Create a new benchmark by Benchmark owner
BENCHMARK=$(curl -s -X POST "http://127.0.0.1:8000/benchmarks/" -H  "accept: application/json" -H  "Authorization: Token $BENCHMARK_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{  \"name\": \"testbenchmark\",  \"description\": \"benchmark-sample\",  \"docs_url\": \"string\",  \"data_preparation_mlcube\": $DATA_PREPROCESSOR_MLCUBE,  \"reference_model_mlcube\": $REFERENCE_MODEL_EXECUTOR_MLCUBE,  \"data_evaluator_mlcube\": $DATA_EVALUATOR_MLCUBE}" | jq -r '.id')

echo "Benchmark Created(by Benchmark Owner). ID: $BENCHMARK"

BENCHMARK_STATUS=$(curl -s -X PUT "http://127.0.0.1:8000/benchmarks/$BENCHMARK/" -H  "accept: application/json" -H  "Authorization: Token $ADMIN_TOKEN" -H  "Content-Type: application/json" -d "{  \"approval_status\": \"APPROVED\"}"| jq -r '.approval_status')

echo "Benchmark Id: $BENCHMARK is marked $BENCHMARK_STATUS (by Admin)"

echo "##########################MODEL OWNER##########################"
# Model Owner Interaction
# Get Model Owner API token(token of testmodelowner user)
MODEL_OWNER_TOKEN=$(curl -s -X POST "http://127.0.0.1:8000/auth-token/" -H  "accept: application/json" -H  "Content-Type: application/json" -d "{  \"username\": \"testmodelowner\",  \"password\": \"test\"}" | jq -r '.token')

echo "Model Owner Token: $MODEL_OWNER_TOKEN"

# Create a model mlcube by Model Owner
MODEL_EXECUTOR1_MLCUBE=$(curl -s -X POST "http://127.0.0.1:8000/mlcubes/" -H  "accept: application/json" -H  "Authorization: Token $MODEL_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{  \"name\": \"model-executor1\",  \"git_mlcube_url\": \"string\", \"git_parameters_url\": \"string\", \"tarball_url\": \"string\",  \"tarball_hash\": \"string\",  \"metadata\": {}}" | jq -r '.id')

echo "Model MLCube Created(by Model Owner). ID: $MODEL_EXECUTOR1_MLCUBE"

# Create another model mlcube by Model Owner
MODEL_EXECUTOR2_MLCUBE=$(curl -s -X POST "http://127.0.0.1:8000/mlcubes/" -H  "accept: application/json" -H  "Authorization: Token $MODEL_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{  \"name\": \"model-executor2\",  \"git_mlcube_url\": \"string\",  \"git_parameters_url\": \"string\", \"tarball_url\": \"string\",  \"tarball_hash\": \"string\",  \"metadata\": {}}" | jq -r '.id')

echo "Model MLCube Created(by Model Owner). ID: $MODEL_EXECUTOR2_MLCUBE"

# Associate the model-executor1 mlcube to the created benchmark by model owner user
MODEL_EXECUTOR1_IN_BENCHMARK=$(curl -s -X POST "http://127.0.0.1:8000/mlcubes/benchmarks/" -H  "accept: application/json" -H  "Authorization: Token $MODEL_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{  \"model_mlcube\": $MODEL_EXECUTOR1_MLCUBE,  \"benchmark\": $BENCHMARK, \"results\": {\"key1\":\"value1\", \"key2\":\"value2\"} }")

echo "Model MlCube Id: $MODEL_EXECUTOR1_MLCUBE associated to Benchmark Id: $BENCHMARK (by Model Owner)"

# Mark the model-executor1 association with created benchmark as approved by benchmark owner
MODEL_EXECUTOR1_IN_BENCHMARK_STATUS=$(curl -s -X PUT "http://127.0.0.1:8000/mlcubes/$MODEL_EXECUTOR1_MLCUBE/benchmarks/$BENCHMARK/" -H  "accept: application/json" -H  "Authorization: Token $BENCHMARK_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{  \"approval_status\": \"APPROVED\"}" | jq -r '.approval_status')

echo "Model MlCube Id: $MODEL_EXECUTOR1_MLCUBE associated to Benchmark Id: $BENCHMARK is marked $MODEL_EXECUTOR1_IN_BENCHMARK_STATUS (by Benchmark Owner)" 

# Associate the model-executor2 mlcube to the created benchmark by model owner user
MODEL_EXECUTOR2_IN_BENCHMARK=$(curl -s -X POST "http://127.0.0.1:8000/mlcubes/benchmarks/" -H  "accept: application/json" -H  "Authorization: Token $MODEL_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{  \"model_mlcube\": $MODEL_EXECUTOR2_MLCUBE,  \"benchmark\": $BENCHMARK, \"results\": {\"key1\":\"value1\", \"key2\":\"value2\"} }")

echo "Model MlCube Id: $MODEL_EXECUTOR2_MLCUBE associated to Benchmark Id: $BENCHMARK (by Model Owner)"

# Mark the model-executor2 association with created benchmark as approved by benchmark owner
MODEL_EXECUTOR2_IN_BENCHMARK_STATUS=$(curl -s -X PUT "http://127.0.0.1:8000/mlcubes/$MODEL_EXECUTOR2_MLCUBE/benchmarks/$BENCHMARK/" -H  "accept: application/json" -H  "Authorization: Token $BENCHMARK_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{  \"approval_status\": \"APPROVED\"}" | jq -r '.approval_status')

echo "Model MlCube Id: $MODEL_EXECUTOR2_MLCUBE associated to Benchmark Id: $BENCHMARK is marked $MODEL_EXECUTOR2_IN_BENCHMARK_STATUS (by Benchmark Owner)"

echo "##########################DATA OWNER##########################"
### Data Owner Interaction
#Get Data Owner API token(token of testdataowner user)
DATASET_OWNER_TOKEN=$(curl -s -X POST "http://127.0.0.1:8000/auth-token/" -H  "accept: application/json" -H  "Content-Type: application/json" -d "{  \"username\": \"testdataowner\",  \"password\": \"test\"}" | jq -r '.token')

echo "Data Owner Token: $MODEL_OWNER_TOKEN"

# Create a dataset by data owner
DATASET=$(curl -s -X POST "http://127.0.0.1:8000/datasets/" -H  "accept: application/json" -H  "Authorization: Token $DATASET_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{  \"name\": \"dataset\",  \"description\": \"dataset-sample\",  \"location\": \"string\",  \"input_data_hash\": \"string\", \"generated_uid\": \"string\",  \"split_seed\": 0,  \"metadata\": {}, \"data_preparation_mlcube\": $DATA_PREPROCESSOR_MLCUBE}" | jq -r '.id') 

echo "Dataset Created(by Data Owner). Id: $DATASET"

# Associate the created dataset to the benchmark by data owner
DATASET_IN_BENCHMARK=$(curl -s -X POST "http://127.0.0.1:8000/datasets/benchmarks/" -H  "accept: application/json" -H  "Authorization: Token $DATASET_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{  \"dataset\": $DATASET,  \"benchmark\": $BENCHMARK}")

echo "Dataset Id: $DATASET associated to Benchmark Id: $BENCHMARK (by Data Owner)"

# Mark the dataset association with created benchmark as approved by benchmark owner
DATASET_IN_BENCHMARK_STATUS=$(curl -s -X PUT "http://127.0.0.1:8000/datasets/$DATASET/benchmarks/$BENCHMARK/" -H  "accept: application/json" -H  "Authorization: Token $BENCHMARK_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{  \"approval_status\": \"APPROVED\"}" | jq -r '.approval_status')

echo "Dataset Id: $DATASET associated to Benchmark Id: $BENCHMARK is marked: $DATASET_IN_BENCHMARK_STATUS (by Benchmark Owner)"

# Once run is complete, create a new result for each model  by data owner
# Create new result for the dataset with model_executor1 mlcube and benchmark 
RESULT1=$(curl -s -X POST "http://127.0.0.1:8000/results/" -H  "accept: application/json" -H  "Authorization: Token $DATASET_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{  \"name\": \"result1\",  \"results\": {\"key1\":\"value1\", \"key2\":\"value2\"},  \"metadata\": {}, \"benchmark\": $BENCHMARK,  \"model\": $MODEL_EXECUTOR1_MLCUBE,  \"dataset\": $DATASET}")

echo "Result created for Benchmark ID: $BENCHMARK  Model ID: $MODEL_EXECUTOR1_MLCUBE Dataset ID: $DATASET (by Data Owner)"

# Create new result for the dataset with model_executor2 mlcube and benchmark 
RESULT2=$(curl -s -X POST "http://127.0.0.1:8000/results/" -H  "accept: application/json" -H  "Authorization: Token $DATASET_OWNER_TOKEN" -H  "Content-Type: application/json" -d "{  \"name\": \"result2\",  \"results\": {\"key1\":\"value1\", \"key2\":\"value2\"},  \"metadata\": {}, \"benchmark\": $BENCHMARK,  \"model\": $MODEL_EXECUTOR2_MLCUBE,  \"dataset\": $DATASET}")

echo "Result created for Benchmark ID: $BENCHMARK  Model ID: $MODEL_EXECUTOR2_MLCUBE Dataset ID: $DATASET (by Data Owner)"
