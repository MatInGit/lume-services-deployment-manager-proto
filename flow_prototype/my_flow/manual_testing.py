import os
import mlflow
from mlflow.tracking import MlflowClient

from model_utils.workflow_base import BaseWorkflow, ExampleChildWorkflow
from model_utils.workflow_builders import WorkflowBuilder

from prefect.blocks.kubernetes import KubernetesClusterConfig
from prefect_kubernetes.credentials import KubernetesCredentials
from prefect_kubernetes.jobs import list_namespaced_job


kubernetes_credentials = (
    KubernetesCredentials()
)  # Create an instance of KubernetesCredentials
with kubernetes_credentials.get_client(
    "core"
) as core_v1_client:  # Use the instance to call get_client
    print(
        core_v1_client.list_namespaced_service()
    )  # Call the list_namespaced_service method on the client

if __name__ == "__main__":
    example = BaseWorkflow(
        workflow_model_name="generic_model",
        workflow_model_version="chanmpion",
        deployment_type="batch",
    )
    print(example.dict())
    results = cluster_credentials_block.list_namespaced_service()
    print(f"Listing mlflow kube svc: {results}")

builder = WorkflowBuilder(example)
