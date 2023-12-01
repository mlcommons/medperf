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

### How tests should work

Each test class should inherit from `MedPerfTest`, which sets up the local authentication and provides utils to create assets (users, datasets, mlcubes, ...)

Each test class contains at least one test function. Both test classes and test class functions can be parameterized. **Each instance of a parameterized test is run independantly**; a new fresh database is used and the class's `SetUp` method is called prior to each test execution.

### Running tests

#### Run the whole tests

To run the whole tests, run:

```bash
python manage.py test
```

use the `--parallel` option to parallelize the tests.

```bash
python manage.py test --parallel
```

#### Run individual files

You can run individual tests files. For example:

```bash
python manage.py test dataset.tests.test_pk
```

#### Run individual tests

Running individual test classes or test functions can be done as follows. Example:

```bash
python manage.py test benchmark.tests.test_ -k BenchmarkPostTest
python manage.py test benchmark.tests.test_ -k test_creation_of_duplicate_name_gets_rejected
```

### Debugging tests

Tests are not "unittests". For example, the test suite for `dataset` relies on the `mlcube` functionalities. This is because the `dataset` tests use utils to create a preparation MLCube for the datasets. When debugging, it might be useful to run test suites in a certain order, and use the `--failfast` option to exit on the first failure. A script is provided for this: `debug_tests.sh`.
