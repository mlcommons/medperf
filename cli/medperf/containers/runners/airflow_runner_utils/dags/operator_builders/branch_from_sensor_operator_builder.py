from medperf.containers.runners.airflow_runner_utils.dags.operator_builders.python_sensor_builder import (
    PythonSensorBuilder,
)
from medperf.containers.runners.airflow_runner_utils.dags.operator_builders.operator_builder import (
    OperatorBuilder,
)
from airflow.decorators import task
from airflow.models.taskinstance import TaskInstance


class BranchFromSensorOperatorBuilder(OperatorBuilder):
    """
    BranchOperators are used together with Sensors to to automatically create branching behavior.
    Once any condition in the sensor is met, it pushes the ID of the corresponding task as an Airflow XCom.
    This BranchOperator then reads this XCom and branches accordingly.
    """

    def __init__(
        self,
        previous_sensor: PythonSensorBuilder,
        **kwargs,
    ):

        self.sensor_task_id = previous_sensor.operator_id
        super().__init__(**kwargs)

    def _define_base_operator(self):

        @task.branch(
            task_id=self.operator_id,
            task_display_name=self.display_name,
            outlets=self.outlets,
        )
        def branching(task_instance: TaskInstance):
            """Read next task from the Sensor XCom (which detected any of the branching conditions)
            and branch into that"""
            xcom_data = task_instance.xcom_pull(task_ids=self.sensor_task_id)
            return [xcom_data]  # This corresponds to the ID of the next task

        return branching()
