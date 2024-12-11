from abc import ABC, abstractmethod
from typing import Union, Tuple
import pandas as pd

from .stage import Stage


class RowStage(Stage, ABC):
    @abstractmethod
    def could_run(self, index: Union[str, int], report: pd.DataFrame) -> bool:
        """Establishes if this step could be executed for the given case

        Args:
            index (Union[str, int]): case index in the report
            report (pd.DataFrame): Dataframe containing the current state of the preparation flow

        Returns:
            bool: wether this stage could be executed
        """

    @abstractmethod
    def execute(
        self, index: Union[str, int], report: pd.DataFrame
    ) -> Tuple[pd.DataFrame, bool]:
        """Executes the stage on the given case

        Args:
            index (Union[str, int]): case index in the report
            report (pd.DataFrame): DataFrame containing the current state of the preparation flow

        Returns:
            pd.DataFrame: Updated report dataframe
            bool: Success status
        """
