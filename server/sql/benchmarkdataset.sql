BEGIN;
--
-- Create model BenchmarkDataset
--
CREATE TABLE "benchmarkdataset_benchmarkdataset" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "approval_status" varchar(100) NOT NULL, "approved_at" datetime NULL, "created_at" datetime NOT NULL, "modified_at" datetime NOT NULL, "benchmark_id" bigint NOT NULL REFERENCES "benchmark_benchmark" ("id") DEFERRABLE INITIALLY DEFERRED, "dataset_id" bigint NOT NULL REFERENCES "dataset_dataset" ("id") DEFERRABLE INITIALLY DEFERRED, "initiated_by_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE INDEX "benchmarkdataset_benchmarkdataset_benchmark_id_c742bec7" ON "benchmarkdataset_benchmarkdataset" ("benchmark_id");
CREATE INDEX "benchmarkdataset_benchmarkdataset_dataset_id_5c825e94" ON "benchmarkdataset_benchmarkdataset" ("dataset_id");
CREATE INDEX "benchmarkdataset_benchmarkdataset_initiated_by_id_2ce37172" ON "benchmarkdataset_benchmarkdataset" ("initiated_by_id");
COMMIT;
