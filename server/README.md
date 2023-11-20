# Server

Documentation TBD

## Writing Tests

Each endpoint must have a test file. An exception is for the endpoints defined in the utils folder, one single file contains tests for all its endpoints.

### Naming conventions

A test file in a module is named according to the relative endpoint it tests. For example, the test files for the `/datasets/` and `/benchmarks/` endpoints (POST and GET list) are named as `test_.py`. The test file for `/results/<pk>/` endpoint is named as `test_pk.py`.

### What to keep in mind when testing

Testing an endpoint means testing, for each HTTP method it supports, the following:
    - Serializer validation rules (`serializers.py`)
    - Database constraints (`models.py`)
    - Permissions (referred to in `views.py`)

Testing is focused on the actions that are not expected to happen, and focuses less on the actions that can happen (as an example, the tests should ensure that an unauthenticated user cannot access an endpoint, but they may not ensure that a certain type of user can edit a certain field.)
