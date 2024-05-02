from prefect import flow, get_run_logger, tags, task
import random
from prefect.blocks.kubernetes import KubernetesClusterConfig
from prefect_kubernetes.credentials import KubernetesCredentials
from prefect_kubernetes.pods import (
    list_namespaced_pod,
    create_namespaced_pod,
    delete_namespaced_pod,
    read_namespaced_pod,
)
from kubernetes.client.models import V1Pod
import uuid
import os
import hashlib
import time

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
    if workflow_instance.deployment_type == "continuous" or "prod":
        logger.info(f"Deploying {workflow_instance.workflow_model_name}")

        set_registered_model_tag(
            workflow_instance.workflow_model_name,
            "deployment_status",
            "deployment_running",
        )

        return workflow_instance

    elif workflow_instance.deployment_type == "batch":
        logger.info(
            f"Deploying {workflow_instance.workflow_model_name} with handler {workflow_instance.deployment_handler_type}"
        )
        logger.info("... running batch job (eventually) ... ")
        return None
    else:
        logger.error(
            f"Invalid deployment type {workflow_instance.deployment_type} for model {workflow_instance.workflow_model_name}"
        )
        return None

@task
def workflow_to_pod(workflow: BaseWorkflow):

    workflow_hash = hashlib.md5(f"{str(workflow.dict())}".encode()).hexdigest()
    logger = get_run_logger()
    logger.info(
        f"Creating pod for {workflow.workflow_model_name} with hash {workflow_hash}"
    )
    unique_id = str(uuid.uuid4())[0:7]
    pod = V1Pod(
        metadata={
            "name": f"{workflow.workflow_model_name}-{workflow.workflow_model_version}-{unique_id}".replace("_", "-"),
            "namespace": "mlflow",
            "labels": {
                "md5chk": workflow_hash,
                "model_name": workflow.workflow_model_name,
                "model_version": workflow.workflow_model_version,
                "service_type": "model_deployment",
            },
        },
        spec={
            "containers": [
                {
                    "name": f"{workflow.workflow_model_name}-{workflow.workflow_model_version}".replace("_", "-"),
                    "image": "matindocker/lumeservicesdeployment:latest", # this can be parameterized to allow for different images
                    "env": [
                        {"name": "model_name", "value": workflow.workflow_model_name},
                        {
                            "name": "model_version",
                            "value": workflow.workflow_model_version,
                        },
                        {
                            "name": "MLFLOW_TRACKING_URI",
                            "value": os.environ.get("MLFLOW_TRACKING_URI"),
                        },
                        {
                            "name": "MLFLOW_TRACKING_USERNAME",
                            "value": os.environ.get("MLFLOW_TRACKING_USERNAME"),
                        },
                        {
                            "name": "MLFLOW_TRACKING_PASSWORD",
                            "value": os.environ.get("MLFLOW_TRACKING_PASSWORD"),
                        },
                        {
                            "name": "MLFLOW_ENABLE_SYSTEM_METRICS_LOGGING",
                            "value": os.environ.get(
                                "MLFLOW_ENABLE_SYSTEM_METRICS_LOGGING"
                            ),
                        },
                        {
                            "name": "AWS_DEFAULT_REGION",
                            "value": os.environ.get("AWS_DEFAULT_REGION"),
                        },
                        {"name": "AWS_REGION", "value": os.environ.get("AWS_REGION")},
                        {
                            "name": "AWS_ACCESS_KEY_ID",
                            "value": os.environ.get("AWS_ACCESS_KEY_ID"),
                        },
                        {
                            "name": "AWS_SECRET_ACCESS_KEY",
                            "value": os.environ.get("AWS_SECRET_ACCESS_KEY"),
                        },
                        {
                            "name": "MLFLOW_S3_ENDPOINT_URL",
                            "value": os.environ.get("MLFLOW_S3_ENDPOINT_URL"),
                        },
                        {
                            "name": "K2EG_PYTHON_CONFIGURATION_PATH_FOLDER",
                            "value": "/opt/deployment/model_manager/src/interfaces",
                        },
                    ],
                }
            ]
        },
    )
    return pod, workflow_hash


@task
def check_if_model_already_exists(
    namespaced_model_list, model_name: str, model_version: str
):
    logger = get_run_logger()
    # logger.info(f"Checking if pod {namespaced_model_list.items} already exists")
    for pod in namespaced_model_list.items:
        # check name and version
        logger.info(f"Checking pod labels: {pod.metadata.labels} ...")
        if (
            pod.metadata.labels.get("model_name") == model_name
            and pod.metadata.labels.get("model_version") == model_version
        ):
            logger.info(
                f"Pod {model_name} already exists with same version {model_version}"
            )
            return True, True, pod
        # name same but version different
        elif (
            pod.metadata.labels.get("model_name") == model_name
            and pod.metadata.labels.get("model_version") != model_version
        ):
            logger.info(f"Pod {model_name} exists but version is different")
            return True, False, pod

    return False, False, None

@flow
def model_manager(models = None):
    logger = get_run_logger()
    
    if models is None:
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
            
    results = []

    for workflow_instance in workflow_instances:
        try:
            logger.info(f"Processing model {workflow_instance.workflow_model_name}")
            results.append(process_model(workflow_instance)) # this doesnt do much anymore
        except Exception as e:
            logger.warning(
                f"Error: {e} for model {workflow_instance.workflow_model_name}"
            )

    logger.info(f"Waiting for model pre-processing to complete")

    namespaced_pod_list = list_namespaced_pod(
        namespace="mlflow",
        kubernetes_credentials=kubernetes_credentials,
    )

    for result in results:
        
        logger.info(f"Processing pod for {result.workflow_model_name}")

        pod, chksum = workflow_to_pod(result)

        already_exists, same_version, old_pod = check_if_model_already_exists(
            namespaced_pod_list,
            result.workflow_model_name,
            result.workflow_model_version,
        )
        
        if result.deployment_terminate:
            if already_exists:
                logger.info(f"Deleting pod {result.workflow_model_name}")
                delete_namespaced_pod(
                    kubernetes_credentials=kubernetes_credentials,
                    pod_name=old_pod.metadata.name,
                    namespace="mlflow",
                )
                set_registered_model_tag(
                    result.workflow_model_name,
                    "deployment_status",
                    "deployment_terminated",
                )
                set_registered_model_tag(
                    result.workflow_model_name,
                    "deployment_pod_name",
                    None
                )
                set_registered_model_tag(
                    result.workflow_model_name,
                    "deployment_type",
                    "terminated"
                )
            else:
                logger.info(f"Pod {result.workflow_model_name} terminated")
        
        else:
            if not already_exists and not same_version:
                logger.info(
                    f"Creating pod {result.workflow_model_name} with version {result.workflow_model_version}"
                )
                create_namespaced_pod(
                    namespace="mlflow",
                    new_pod=pod,
                    kubernetes_credentials=kubernetes_credentials,
                )
                
                set_registered_model_tag(
                    result.workflow_model_name,
                    "deployment_status",
                    "deployment_running",
                )
                set_registered_model_tag(
                    result.workflow_model_name,
                    "deployment_pod_name",
                    pod.metadata["name"] # its annoying this is different
                )
                # human readable timestamp
                set_registered_model_tag(
                    result.workflow_model_name,
                    "deployment_timestamp",
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                )

            elif already_exists and not same_version:
                logger.info(f"Deleting pod {result.workflow_model_name}")
                delete_namespaced_pod(
                    kubernetes_credentials=kubernetes_credentials,
                    pod_name=old_pod.metadata.name,
                    namespace="mlflow",
                )
                set_registered_model_tag(
                    result.workflow_model_name,
                    "deployment_status",
                    "updating_deployment",
                )
                
                create_namespaced_pod(
                    namespace="mlflow",
                    new_pod=pod,
                    kubernetes_credentials=kubernetes_credentials,
                )
                set_registered_model_tag(
                    result.workflow_model_name,
                    "deployment_status",
                    "deployment_running",
                )
                set_registered_model_tag(
                    result.workflow_model_name,
                    "deployment_pod_name",
                    pod.metadata["name"] # its annoying this is different
                )
            

            else:
                logger.info(
                    f"Pod {result.workflow_model_name} with version {result.workflow_model_version} already exists"
                )

    # also handle hanging pods that are not in the list


if __name__ == "__main__":
    with tags("local"):
        model_manager.run()
