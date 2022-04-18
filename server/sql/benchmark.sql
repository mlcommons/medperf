BEGIN;
--
-- Create model Benchmark
--
CREATE TABLE "benchmark_benchmark" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(20) NOT NULL UNIQUE, "description" varchar(100) NOT NULL, "docs_url" varchar(100) NOT NULL, "demo_dataset_tarball_url" varchar(256) NOT NULL, "demo_dataset_tarball_hash" varchar(100) NOT NULL, "demo_dataset_generated_uid" varchar(128) NOT NULL, "metadata" text NULL CHECK ((JSON_VALID("metadata") OR "metadata" IS NULL)), "state" varchar(100) NOT NULL, "is_valid" bool NOT NULL, "is_active" bool NOT NULL, "approval_status" varchar(100) NOT NULL, "user_metadata" text NULL CHECK ((JSON_VALID("user_metadata") OR "user_metadata" IS NULL)), "approved_at" datetime NULL, "created_at" datetime NOT NULL, "modified_at" datetime NOT NULL, "data_evaluator_mlcube_id" bigint NOT NULL REFERENCES "mlcube_mlcube" ("id") DEFERRABLE INITIALLY DEFERRED, "data_preparation_mlcube_id" bigint NOT NULL REFERENCES "mlcube_mlcube" ("id") DEFERRABLE INITIALLY DEFERRED, "owner_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "reference_model_mlcube_id" bigint NOT NULL REFERENCES "mlcube_mlcube" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE INDEX "benchmark_benchmark_data_evaluator_mlcube_id_84cb99f9" ON "benchmark_benchmark" ("data_evaluator_mlcube_id");
CREATE INDEX "benchmark_benchmark_data_preparation_mlcube_id_d2ad0ef3" ON "benchmark_benchmark" ("data_preparation_mlcube_id");
CREATE INDEX "benchmark_benchmark_owner_id_94b62928" ON "benchmark_benchmark" ("owner_id");
CREATE INDEX "benchmark_benchmark_reference_model_mlcube_id_196acf26" ON "benchmark_benchmark" ("reference_model_mlcube_id");
COMMIT;
