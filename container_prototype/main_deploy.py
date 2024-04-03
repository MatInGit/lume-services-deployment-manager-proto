from model_utils.utils import MLflowModelGetter, VaraibleTransformer
import os, json, time
from k2eg_utils.utils import monitor, initialise_k2eg
from sklearn.datasets import fetch_openml
import sys
import torch

_dir = os.path.dirname(os.path.abspath(__file__))
os.environ['K2EG_PYTHON_CONFIGURATION_PATH_FOLDER'] = os.path.join(_dir, "k2eg_utils")

model_getter = MLflowModelGetter(model_name="lcls-cu-inj-nn", model_version="champion") # these will be grabbed from the environment variables
model = model_getter.get_model()
pv_mapping = model_getter.get_pv_mapping()
vt = VaraibleTransformer(pv_mapping["mappings"], pv_mapping["epics_vars"].keys())

pv_list = []

for key, value in pv_mapping["epics_vars"].items():
    pv_list.append(value["source"])
    
print(pv_list)

# handler gets pvs
# maps them to model inputs according to pv_mappings.json
# calls model.evaluate(inputs)
# sends the output to specified pvs according to pv_mappings.json


if __name__ == "__main__":
      # returns mlflow.pyfunc.PyFuncModel
    print("initialising k2eg")
    k = initialise_k2eg()  
    print("k2eg initialised")
    
    # intialise pv values 
    for pv in pv_list:
        pv_full = k.get(pv)
        val = pv_full['value']
        print(f"PV: {pv}, Value: {val}")
        vt.handler_for_k2eg(pv, pv_full)

    monitor(pv_list=pv_list, handler=vt.handler_for_k2eg, client=k)

    while True:
        if vt.updated:
            inputs = vt.latest_transformed
            print(f"Inputs: {inputs}")
            
            if model_getter.model_type == "torch":
                for key, value in inputs.items():
                    inputs[key] = torch.tensor(value, dtype=torch.float32)
        
            output = model.evaluate(inputs)
            print(f"Output: {output}")
            vt.updated = False
        
        time.sleep(1)
                
        