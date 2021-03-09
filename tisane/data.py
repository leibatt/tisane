import os
import pandas as pd 
from typing import Union

def absolute_path(p: str) -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), p)

class Dataset(object): 
    # data_vectors: dict
    dataset : pd.DataFrame

    # Takes input in either a CSV or a Pandas DataFrame
    def __init__(self, source: Union[str, pd.DataFrame]): 
        df = None 
        # Read in data 
        if isinstance(source, str): 
            abs_path = absolute_path(p=source)
            df = pd.read_csv(abs_path)
        elif isinstance(source, pd.DataFrame): 
            df = source 

        # TODO: post-processing? E.g., break up into DataVectors?
        self.dataset = df


class DataVector(object): 
    name: str
    values: pd.DataFrame 

    # def __init__(self, name: str, values: pd.DataFrame): 
    #     self.name = name
    #     self.values = values

    def get_cardinality(self): 
        pass