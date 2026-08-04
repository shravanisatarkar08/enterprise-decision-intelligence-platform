import pandas as pd


class DataStore:
    """
    Stores uploaded datasets in memory.

    Later this can be replaced with Redis,
    PostgreSQL or a Vector Database.
    """

    def __init__(self):
        self.datasets = {}

    def save_dataset(self, dataset_id: str, dataframe: pd.DataFrame):
        self.datasets[dataset_id] = dataframe

    def get_dataset(self, dataset_id: str):
        return self.datasets.get(dataset_id)
data_store = DataStore()