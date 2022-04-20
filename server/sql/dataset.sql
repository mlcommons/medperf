BEGIN;
--
-- Create model Dataset
--
CREATE TABLE "dataset_dataset" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(20) NOT NULL, "description" varchar(20) NOT NULL, "location" varchar(100) NOT NULL, "input_data_hash" varchar(128) NOT NULL, "generated_uid" varchar(128) NOT NULL UNIQUE, "split_seed" integer NOT NULL, "is_valid" bool NOT NULL, "state" varchar(100) NOT NULL, "generated_metadata" text NULL CHECK ((JSON_VALID("generated_metadata") OR "generated_metadata" IS NULL)), "user_metadata" text NULL CHECK ((JSON_VALID("user_metadata") OR "user_metadata" IS NULL)), "created_at" datetime NOT NULL, "modified_at" datetime NOT NULL, "data_preparation_mlcube_id" bigint NOT NULL REFERENCES "mlcube_mlcube" ("id") DEFERRABLE INITIALLY DEFERRED, "owner_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE INDEX "dataset_dataset_data_preparation_mlcube_id_bd2d1718" ON "dataset_dataset" ("data_preparation_mlcube_id");
CREATE INDEX "dataset_dataset_owner_id_a46ec1ab" ON "dataset_dataset" ("owner_id");
COMMIT;
