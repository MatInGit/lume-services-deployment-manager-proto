from mlflow import MlflowClient
import mlflow
import os, json, time

# json_data = json.load(open("cred.json"))

# os.environ["MLFLOW_TRACKING_USERNAME"] = json_data["MLFLOW_TRACKING_USERNAME"]
# os.environ["MLFLOW_TRACKING_PASSWORD"] = json_data["MLFLOW_TRACKING_PASSWORD"]
# os.environ["MLFLOW_ENABLE_SYSTEM_METRICS_LOGGING"] = json_data[
#     "MLFLOW_ENABLE_SYSTEM_METRICS_LOGGING"
# ]
# os.environ["AWS_DEFAULT_REGION"] = json_data["AWS_DEFAULT_REGION"]
# os.environ["AWS_REGION"] = json_data["AWS_REGION"]
# os.environ["AWS_ACCESS_KEY_ID"] = json_data["AWS_ACCESS_KEY_ID"]
# os.environ["AWS_SECRET_ACCESS_KEY"] = json_data["AWS_SECRET_ACCESS_KEY"]
# os.environ["MLFLOW_S3_ENDPOINT_URL"] = json_data["MLFLOW_S3_ENDPOINT_URL"]
# # tracking uri
# os.environ["MLFLOW_TRACKING_URI"] = json_data["MLFLOW_TRACKING_URI"]

class DepGetter:
    def __init__(self, model_name: str, model_version):
        self.model_name = model_name
        self.model_version = model_version
        self.client = MlflowClient()
    def get_dependencies(self):
        # Get dependencies
        if type(self.model_version) == int:
            version = self.client.get_model_version(self.model_name, self.model_version)
        elif type(self.model_version) == str:
            version_no = self.client.get_model_version_by_alias(
                self.model_name, self.model_version
            )
            version = self.client.get_model_version(self.model_name, version_no.version)
            

        deps = mlflow.artifacts.download_artifacts(f"{version.source}/requirements.txt")
        return deps
    

dep = DepGetter("torch_model", "champion") # these will be grabbed from the environment variables

# print(dep.get_dependencies())

os.system(f"pip install -r {dep.get_dependencies()}")
os.system("python ./main_deploy.py")