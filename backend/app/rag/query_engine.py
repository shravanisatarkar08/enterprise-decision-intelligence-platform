import pandas as pd

from app.rag.query_parser import QueryParser
from app.rag.query_executor import QueryExecutor


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

    def execute_rule_based_query(self, question: str):

        question = question.lower()

        if "rows" in question:
            return f"The dataset contains {len(self.df)} rows."

        if "columns" in question:
            return (
                f"The dataset has {len(self.df.columns)} columns: "
                + ", ".join(self.df.columns)
            )

        if "missing" in question:
            return str(self.df.isnull().sum().to_dict())

        if "duplicate" in question:
            return f"Duplicate rows: {self.df.duplicated().sum()}"

        return None

    def execute_smart_query(self, question: str):

        parser = QueryParser()

        parsed = parser.parse(
            question,
            self.df.columns.tolist()
        )

        executor = QueryExecutor(self.df)

        return executor.execute(
            parsed["operation"],
            parsed["column"]
        )