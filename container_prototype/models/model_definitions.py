import mlflow
from mlflow.models.model import get_model_info
from mlflow import MlflowClient
import pprint
import pandas as pd
import os
import pip

from lume_model.models import TorchModule


class MLflowModelGetter:
    def __init__(self, model_name: str, model_version: str):
        self.model_name = model_name
        self.model_version = model_version
        self.client = MlflowClient()

    def get_model(self):

        if type(self.model_version) == int:
            version = self.client.get_model_version(self.model_name, self.model_version)
        elif type(self.model_version) == str:
            version_no = self.client.get_model_version_by_alias(
                self.model_name, self.model_version
            )
            version = self.client.get_model_version(self.model_name, version_no.version)

        # flavor
        flavor = get_model_info(model_uri=version.source).flavors
        loader_module = flavor["python_function"]["loader_module"]
        print(f"Loader module: {loader_module}")

        if loader_module == "mlflow.pyfunc.model":
            print("Loading pyfunc model")
            model_pyfunc = mlflow.pyfunc.load_model(model_uri=version.source)
            model = model_pyfunc.unwrap_python_model().get_lume_model()
            print(f"Model: {model}, Model type: {type(model)}")
            return model

        elif loader_module == "mlflow.pytorch":
            print("Loading torch model")
            model_torch_module = mlflow.pytorch.load_model(model_uri=version.source)
            model = model_torch_module.model
            print(f"Model: {model}, Model type: {type(model)}")
            return model
        else:
            raise Exception(f"Flavor {flavor} not supported")
