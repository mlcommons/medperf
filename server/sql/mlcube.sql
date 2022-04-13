BEGIN;
--
-- Create model MlCube
--
CREATE TABLE "mlcube_mlcube" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(20) NOT NULL UNIQUE, "git_mlcube_url" varchar(256) NOT NULL, "git_parameters_url" varchar(256) NOT NULL, "tarball_url" varchar(256) NOT NULL, "tarball_hash" varchar(100) NOT NULL, "state" varchar(100) NOT NULL, "is_valid" bool NOT NULL, "metadata" text NULL CHECK ((JSON_VALID("metadata") OR "metadata" IS NULL)), "user_metadata" text NULL CHECK ((JSON_VALID("user_metadata") OR "user_metadata" IS NULL)), "created_at" datetime NOT NULL, "modified_at" datetime NOT NULL, "owner_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE INDEX "mlcube_mlcube_owner_id_e561043a" ON "mlcube_mlcube" ("owner_id");
COMMIT;
