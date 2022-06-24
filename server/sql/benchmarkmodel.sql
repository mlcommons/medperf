BEGIN;
--
-- Create model BenchmarkModel
--
CREATE TABLE "benchmarkmodel_benchmarkmodel" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "results" text NOT NULL CHECK ((JSON_VALID("results") OR "results" IS NULL)), "approval_status" varchar(100) NOT NULL, "approved_at" datetime NULL, "created_at" datetime NOT NULL, "modified_at" datetime NOT NULL, "benchmark_id" bigint NOT NULL REFERENCES "benchmark_benchmark" ("id") DEFERRABLE INITIALLY DEFERRED, "initiated_by_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "model_mlcube_id" bigint NOT NULL REFERENCES "mlcube_mlcube" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE INDEX "benchmarkmodel_benchmarkmodel_benchmark_id_28f84f96" ON "benchmarkmodel_benchmarkmodel" ("benchmark_id");
CREATE INDEX "benchmarkmodel_benchmarkmodel_initiated_by_id_006bc92a" ON "benchmarkmodel_benchmarkmodel" ("initiated_by_id");
CREATE INDEX "benchmarkmodel_benchmarkmodel_model_mlcube_id_fcf25344" ON "benchmarkmodel_benchmarkmodel" ("model_mlcube_id");
COMMIT;
