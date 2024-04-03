from mlflow import MlflowClient
import mlflow
import os, json, time
from model_utils.utils import DepGetter

dep = DepGetter(
    os.environ["model_name"], os.environ["model_version"]
)  # these will be grabbed from the environment variables

os.system(f"pip install -r {dep.get_dependencies()} --no-cache-dir")
os.system("python ./main_deploy.py")
