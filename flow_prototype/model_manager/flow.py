from prefect import flow, get_run_logger, tags, task
import random
from prefect.blocks.kubernetes import KubernetesClusterConfig
from prefect_kubernetes.credentials import KubernetesCredentials
from prefect_kubernetes.pods import list_namespaced_pod
from prefect_kubernetes.pods import create_namespaced_pod
from kubernetes.client.models import V1Pod
import uuid
import os
import hashlib

from model_utils.workflow_base import BaseWorkflow  # base class for workflow
from flow_utils.mlflow_flow import (
    get_models,
    get_by_model_aliases,
    set_registered_model_tag,
)  # all mlflow related stuff

kubernetes_credentials = (
    KubernetesCredentials()
)  # Create an instance of KubernetesCredentials


@task
def process_model(workflow_instance: BaseWorkflow):
    logger = get_run_logger()
    if workflow_instance.deployment_type == "continuous":
        logger.info(f"Deploying {workflow_instance.workflow_model_name}")

        # handler = get_handler_by_falvor(workflow_instance.deployment_handler_type)
        # handler.deploy(workflow_instance) # spins up a k8s pod with the model
        # pod_name = handler.get_pod_name(workflow_instance)

        set_registered_model_tag(
            workflow_instance.workflow_model_name,
            "deployment_status",
            "starting_deployment",
        )
        
        return workflow_instance

    elif workflow_instance.deployment_type == "batch":
        logger.info(
            f"Deploying {workflow_instance.workflow_model_name} with handler {workflow_instance.deployment_handler_type}"
        )
        logger.info("... running batch job (eventually) ... ")
        # exectute get data
        # execute model with data
        # save results to user specified location
        return None
    else:
        logger.error(
            f"Invalid deployment type {workflow_instance.deployment_type} for model {workflow_instance.workflow_model_name}"
        )
        return None
###{
#     "MLFLOW_TRACKING_USERNAME": "admin",
#     "MLFLOW_TRACKING_PASSWORD": "password",
#     "MLFLOW_ENABLE_SYSTEM_METRICS_LOGGING": "true",
#     "AWS_DEFAULT_REGION": "eu-west-3",
#     "AWS_REGION": "eu-west-3",
#     "AWS_ACCESS_KEY_ID": "admin",
#     "AWS_SECRET_ACCESS_KEY": "test_password",
#     "MLFLOW_S3_ENDPOINT_URL": "http://172.24.5.222:9020",
#     "MLFLOW_TRACKING_URI": "https://ard-mlflow.slac.stanford.edu"
#   }
  

@task
def workflow_to_pod(workflow: BaseWorkflow):

    
    workflow_hash = hashlib.md5(f"{str(workflow.dict())}".encode()).hexdigest()
    logger = get_run_logger()
    logger.info(f"Creating pod for {workflow.workflow_model_name} with hash {workflow_hash}")
    
    pod = V1Pod(
        metadata={"name": f"{workflow.workflow_model_name}-{workflow.workflow_model_version}-{workflow_hash}", "namespace": "mlflow", "labels":{"md5chk": workflow_hash}},
        spec={
            "containers": [
                {
                    "name": f"{workflow.workflow_model_name}-{workflow.workflow_model_version}",
                    "image": "matindocker/lumeservicesdeployment:latest",
                    "env": [
                        {"name": "model_name", "value": workflow.workflow_model_name},
                        {
                            "name": "model_version",
                            "value": workflow.workflow_model_version,
                        },
                        {"name": "MLFLOW_TRACKING_URI", "value": os.environ.get("MLFLOW_TRACKING_URI")},
                        {"name": "MLFLOW_TRACKING_USERNAME", "value": os.environ.get("MLFLOW_TRACKING_USERNAME")},
                        {"name": "MLFLOW_TRACKING_PASSWORD", "value": os.environ.get("MLFLOW_TRACKING_PASSWORD")},
                        {"name": "MLFLOW_ENABLE_SYSTEM_METRICS_LOGGING", "value": os.environ.get("MLFLOW_ENABLE_SYSTEM_METRICS_LOGGING")},
                        {"name": "AWS_DEFAULT_REGION", "value": os.environ.get("AWS_DEFAULT_REGION")},
                        {"name": "AWS_REGION", "value": os.environ.get("AWS_REGION")},
                        {"name": "AWS_ACCESS_KEY_ID", "value": os.environ.get("AWS_ACCESS_KEY_ID")},
                        {"name": "AWS_SECRET_ACCESS_KEY", "value": os.environ.get("AWS_SECRET_ACCESS_KEY")},
                        {"name": "MLFLOW_S3_ENDPOINT_URL", "value": os.environ.get("MLFLOW_S3_ENDPOINT_URL")},
                        
                    ],
                }
            ]
        },
    )
    return pod, workflow_hash
@task
def check_if_model_already_exists(namespaced_model_list,chcksum):
    logger = get_run_logger()
    logger.info(f"Checking if pod {namespaced_model_list.items} already exists")
    for pod in namespaced_model_list.items:
        if pod.metadata.labels.get("md5chk") == chcksum:
            logger.error(f"Pod {pod.metadata.name} already exists")
            return True,pod.metadata.name
    return False, None

@flow
def model_manager():
    logger = get_run_logger()

    models = get_models()
    model_dicts = get_by_model_aliases(models)
    workflow_instances = []

    # validate configs and create workflow instances

    for model_dict in model_dicts:
        try:
            workflow_instance = BaseWorkflow(**model_dict)
            workflow_instances.append(workflow_instance)
        except Exception as e:
            logger.warning(f"Error: {e} for model {model_dict['workflow_model_name']}")

    __futures = []
    for workflow_instance in workflow_instances:
        try:
            logger.info(f"Processing model {workflow_instance.workflow_model_name}")
            result = process_model.submit(workflow_instance)
            __futures.append(result)
        except Exception as e:
            logger.warning(
                f"Error: {e} for model {workflow_instance.workflow_model_name}"
            )

    logger.info(f"Waiting for model pre-processing to complete")

    results = []
    while len(__futures) > len(results):
        for future in __futures:
            result = future.wait(0.1)
            # need to consider if this is try/except
            if result:
                results.append(result.result())
    
    namespaced_pod_list = list_namespaced_pod(
            namespace="prefect",
            kubernetes_credentials=kubernetes_credentials,
        )
    
    for result in results:
        
        pod, chksum = workflow_to_pod(result)

        already_exists,_ = check_if_model_already_exists(namespaced_pod_list, chksum)

        logger.info(f"Checking if pod {result.workflow_model_name} already exists in list {namespaced_pod_list}")
        
        if not already_exists:
            create_namespaced_pod(
                namespace="mlflow",
                new_pod=pod,
                kubernetes_credentials=kubernetes_credentials,
            )



if __name__ == "__main__":
    with tags("local"):
        model_manager.run()
