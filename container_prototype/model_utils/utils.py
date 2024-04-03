import mlflow
from mlflow.models.model import get_model_info
from mlflow import MlflowClient
import pandas as pd
import yaml
import sympy as sp

from lume_model.models import TorchModule, TorchModel


class MLflowModelGetter:
    def __init__(self, model_name: str, model_version: str):
        self.model_name = model_name
        self.model_version = model_version
        self.client = MlflowClient()
        self.model_type = None
        
        
    def get_pv_mapping(self):
        
        if type(self.model_version) == int:
            version = self.client.get_model_version(self.model_name, self.model_version)
        elif type(self.model_version) == str:
            version_no = self.client.get_model_version_by_alias(
                self.model_name, self.model_version
            )
            version = self.client.get_model_version(self.model_name, version_no.version)

        # download pv_mappings.yaml from model root
        self.client.download_artifacts(version.run_id, f"{self.model_name}/pv_mapping.yaml", ".")
        return yaml.load(open(f"{self.model_name}/pv_mapping.yaml", "r"), Loader=yaml.FullLoader)

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
            self.model_type = "pyfunc"
            return model

        elif loader_module == "mlflow.pytorch":
            print("Loading torch model")
            model_torch_module = mlflow.pytorch.load_model(model_uri=version.source)
            assert isinstance(model_torch_module, TorchModule)
            model = model_torch_module.model
            assert isinstance(model, TorchModel)
            print(f"Model: {model}, Model type: {type(model)}")
            self.model_type = "torch"
            return model
        else:
            raise Exception(f"Flavor {flavor} not supported")


class VaraibleTransformer():
    def __init__(self, pv_mapping: dict, symbol_list):
        self.pv_mapping = pv_mapping
        
        for key, value in self.pv_mapping.items():
            self.__validate_formula(value["formula"])
        self.latest_pvs = {symbol: None for symbol in symbol_list}
        self.latest_transformed = {key: None for key in self.pv_mapping.keys()}
        self.updated = False
    
    def __validate_formula(self, formula: str):
        try:
            sp.sympify(formula.replace(":", "_"))
        except:
            raise Exception(f"Invalid formula: {formula}")
        
    def handler_for_k2eg(self,pv_name, value):
        
        # strip protoco; ca:// or pva:// from pv_name if present
        if pv_name.startswith("ca://"):
            pv_name = pv_name[5:]
        elif pv_name.startswith("pva://"):
            pv_name = pv_name[6:]
        else:
            pass
        
        self.latest_pvs[pv_name] = value["value"]
        #print(self.latest_pvs)
        if all([value is not None for value in self.latest_pvs.values()]):
            # print("All PVs updated")
            self.transform()
            
        
    def transform(self):
        transformed = {}
        pvs_renamed = {key.replace(":", "_"): value for key, value in self.latest_pvs.items()}
        for key, value in self.pv_mapping.items():
            transformed[key] = sp.sympify(value["formula"].replace(":", "_")).subs(pvs_renamed)
        
        for key, value in transformed.items():
            self.latest_transformed[key] = value
        self.updated = True