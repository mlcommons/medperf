BEGIN;
--
-- Create model ModelResult
--
CREATE TABLE "result_modelresult" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(20) NOT NULL, "results" text NOT NULL CHECK ((JSON_VALID("results") OR "results" IS NULL)), "metadata" text NOT NULL CHECK ((JSON_VALID("metadata") OR "metadata" IS NULL)), "approval_status" varchar(100) NOT NULL, "approved_at" datetime NULL, "created_at" datetime NOT NULL, "modified_at" datetime NOT NULL, "benchmark_id" bigint NOT NULL REFERENCES "benchmark_benchmark" ("id") DEFERRABLE INITIALLY DEFERRED, "dataset_id" bigint NOT NULL REFERENCES "dataset_dataset" ("id") DEFERRABLE INITIALLY DEFERRED, "model_id" bigint NOT NULL REFERENCES "mlcube_mlcube" ("id") DEFERRABLE INITIALLY DEFERRED, "owner_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE UNIQUE INDEX "result_modelresult_benchmark_id_model_id_dataset_id_674bd97d_uniq" ON "result_modelresult" ("benchmark_id", "model_id", "dataset_id");
CREATE INDEX "result_modelresult_benchmark_id_a69485e9" ON "result_modelresult" ("benchmark_id");
CREATE INDEX "result_modelresult_dataset_id_29ddd7af" ON "result_modelresult" ("dataset_id");
CREATE INDEX "result_modelresult_model_id_3b100f16" ON "result_modelresult" ("model_id");
CREATE INDEX "result_modelresult_owner_id_3db08c8b" ON "result_modelresult" ("owner_id");
COMMIT;
