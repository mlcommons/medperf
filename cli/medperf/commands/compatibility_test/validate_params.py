from medperf.exceptions import InvalidArgumentError, MedperfException


class CompatibilityTestParamsValidator:
    """Validates the input parameters to the CompatibilityTestExecution class"""

    def __init__(
        self,
        benchmark: int = None,
        data_prep: str = None,
        model: str = None,
        evaluator: str = None,
        data_uid: str = None,
    ):
        self.benchmark_uid = benchmark
        self.data_prep = data_prep
        self.model = model
        self.evaluator = evaluator
        self.data_uid = data_uid

    def __validate_cubes(self):
        if not self.model and not self.benchmark_uid:
            raise InvalidArgumentError(
                "A model or a benchmark should at least be specified"
            )

        if not self.evaluator and not self.benchmark_uid:
            raise InvalidArgumentError(
                "A metrics container or a benchmark should at least be specified"
            )

    def __validate_prepared_data_source(self):
        if self.data_prep:
            raise InvalidArgumentError(
                "A data preparation container is not needed when specifying a prepared dataset"
            )

    def __validate_data_source(self):
        if self.data_uid:
            self.__validate_prepared_data_source()
            return

        if self.benchmark_uid:
            return

        msg = "A data source should at least be specified, either by providing"
        msg += " a prepared data uid or a benchmark"
        raise InvalidArgumentError(msg)

    def __validate_redundant_benchmark(self):
        if not self.benchmark_uid:
            return

        redundant_bmk_demo = self.data_uid is not None
        redundant_bmk_model = self.model is not None
        redundant_bmk_evaluator = self.evaluator is not None
        redundant_bmk_preparator = (
            self.data_prep is not None or self.data_uid is not None
        )
        if all(
            [
                redundant_bmk_demo,
                redundant_bmk_model,
                redundant_bmk_evaluator,
                redundant_bmk_preparator,
            ]
        ):
            raise InvalidArgumentError("The provided benchmark will not be used")

    def validate(self):
        """Ensures test has been passed a valid combination of parameters.
        Raises `medperf.exceptions.InvalidArgumentError` when the parameters are
        invalid.
        """

        self.__validate_cubes()
        self.__validate_data_source()
        self.__validate_redundant_benchmark()

    def get_data_source(self):
        """Parses the input parameters and returns a string, one of:
        "prepared", if the source of data is a prepared dataset uid,
        "benchmark", if the source of data is the demo dataset of a benchmark.


        This function assumes the passed parameters to the constructor have been already
        validated.
        """
        if self.data_uid:
            return "prepared"

        if self.benchmark_uid:
            return "benchmark"

        raise MedperfException(
            "Ensure calling the `validate` method before using this method"
        )
