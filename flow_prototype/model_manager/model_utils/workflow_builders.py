from .workflow_base import BaseWorkflow
import pprint


class WorkflowBuilder:
    # def __init__(self, workflow_instance: BaseWorkflow):
    #     self.workflow_instance = workflow_instance
    # accept anything with parent class BaseWorkflow
    def __init__(self, workflow: BaseWorkflow) -> None:
        self.workflow = workflow
