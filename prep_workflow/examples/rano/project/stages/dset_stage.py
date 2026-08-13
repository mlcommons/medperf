from abc import ABC, abstractmethod
import pandas as pd
from typing import Tuple

from .stage import Stage


class DatasetStage(Stage, ABC):

    @abstractmethod
    def execute(self, report: pd.DataFrame) -> Tuple[pd.DataFrame, bool]:
        """Executes the stage

        Args:
            index (Union[str, int]): case index in the report
            report (pd.DataFrame): DataFrame containing the current state of the preparation flow

        Returns:
            pd.DataFrame: Updated report dataframe
            bool: Success status
        """
