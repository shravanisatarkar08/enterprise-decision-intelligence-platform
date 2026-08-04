import pandas as pd


class QueryExecutor:

    def __init__(self, dataframe: pd.DataFrame):
        self.df = dataframe

    def execute(self, operation: str, column: str):

        if column is None:
            return None

        if column not in self.df.columns:
            return None

        try:

            if operation == "max":

                row = self.df.loc[self.df[column].idxmax()]

                return (
                    f"{row['Name']} has the highest "
                    f"{column} of {row[column]}."
                )

            elif operation == "min":

                row = self.df.loc[self.df[column].idxmin()]

                return (
                    f"{row['Name']} has the lowest "
                    f"{column} of {row[column]}."
                )

            elif operation == "mean":

                return (
                    f"The average {column} is "
                    f"{round(self.df[column].mean(),2)}."
                )

            elif operation == "count":

                return (
                    f"The dataset contains "
                    f"{self.df[column].count()} values in {column}."
                )

        except Exception:
            return None

        return None