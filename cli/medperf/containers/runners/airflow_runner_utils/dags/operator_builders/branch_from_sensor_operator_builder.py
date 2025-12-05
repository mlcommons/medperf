from .python_sensor_builder import PythonSensorBuilder
from .operator_builder import OperatorBuilder
from airflow.decorators import task
from airflow.models.taskinstance import TaskInstance


class BranchFromSensorOperatorBuilder(OperatorBuilder):

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
            print(f"{self.next_ids=}")
            xcom_data = task_instance.xcom_pull(task_ids=self.sensor_task_id)
            return [xcom_data]

        return branching()
