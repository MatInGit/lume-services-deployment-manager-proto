from models.model_definitions import MLflowModelGetter
import os, json, time
import random

from sklearn.datasets import fetch_openml


json_data = json.load(open("cred.json"))

os.environ["MLFLOW_TRACKING_USERNAME"] = json_data["MLFLOW_TRACKING_USERNAME"]
os.environ["MLFLOW_TRACKING_PASSWORD"] = json_data["MLFLOW_TRACKING_PASSWORD"]
os.environ["MLFLOW_ENABLE_SYSTEM_METRICS_LOGGING"] = json_data[
    "MLFLOW_ENABLE_SYSTEM_METRICS_LOGGING"
]
os.environ["AWS_DEFAULT_REGION"] = json_data["AWS_DEFAULT_REGION"]
os.environ["AWS_REGION"] = json_data["AWS_REGION"]
os.environ["AWS_ACCESS_KEY_ID"] = json_data["AWS_ACCESS_KEY_ID"]
os.environ["AWS_SECRET_ACCESS_KEY"] = json_data["AWS_SECRET_ACCESS_KEY"]
os.environ["MLFLOW_S3_ENDPOINT_URL"] = json_data["MLFLOW_S3_ENDPOINT_URL"]
# tracking uri
os.environ["MLFLOW_TRACKING_URI"] = json_data["MLFLOW_TRACKING_URI"]


model_getter = MLflowModelGetter(model_name="torch_model", model_version="champion")

if __name__ == "__main__":
    model = model_getter.get_model()  # returns mlflow.pyfunc.PyFuncModel

    print("Model is running")
    while True:

        random_input = {"x1": random.random(), "x2": random.random()}
        time.sleep(1)
        print(random_input)
        print(model.evaluate(random_input))
