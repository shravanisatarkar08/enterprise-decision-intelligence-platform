import pandas as pd


class QueryEngine:

    def __init__(self, dataframe: pd.DataFrame):
        self.df = dataframe

    def get_dataset_summary(self):

        return {
            "rows": len(self.df),
            "columns": self.df.columns.tolist(),
            "data_types": self.df.dtypes.astype(str).to_dict(),
            "missing_values": self.df.isnull().sum().to_dict(),
            "sample_rows": self.df.head(5).to_dict(orient="records")
        }