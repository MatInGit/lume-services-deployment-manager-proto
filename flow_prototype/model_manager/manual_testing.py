import os
import mlflow
from mlflow.tracking import MlflowClient

from model_utils.workflow_base import BaseWorkflow, ExampleChildWorkflow
from model_utils.workflow_builders import WorkflowBuilder

from cookiecutter.main import cookiecutter
import pprint


def map_names_to_templates(workflow_config: dict):
    new_dict = {}
    for key, value in workflow_config.items():
        if key == "workflow_model_name":
            new_dict["model_name"] = value
            new_dict["project_name"] = value
        elif key == "workflow_model_version":
            new_dict["model_version"] = value
    return new_dict


if __name__ == "__main__":
    # minimum deployment
    example = BaseWorkflow(
        workflow_model_name="generic_model",
        workflow_model_version="champion",
        deployment_type="continuous",
    )

    # make project using cookiecutter
    context = map_names_to_templates(example.dict().copy())

    template_dir = "./model_manager/templates"
    output_dir = "./generated_projects"
    cookiecutter(
        template_dir,
        output_dir=output_dir,
        no_input=True,
        extra_context=context,
        overwrite_if_exists=True,
    )

    # run pytest
    os.system("cd generated_projects/generic_model && pytest")
