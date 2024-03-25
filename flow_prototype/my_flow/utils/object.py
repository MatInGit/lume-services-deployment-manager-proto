import pydantic
from pydantic import (
    BaseModel,
    ValidationError,
    AnyUrl,
    field_validator,
    PositiveInt,
    validator,
)
from typing import List, Optional


class BaseWorkflow(BaseModel):
    workflow_model_name: str
    workflow_model_version: str
    deployment_type: str
    retrain: Optional[bool | None]
    retrain_endpoint: Optional[AnyUrl | None]
    lattice_component: Optional[str]
    lume_service: Optional[bool | None] = None
    lume_service_url: Optional[AnyUrl | None] = None
    maintainer: Optional[str | None] = None
    deplyment_status: Optional[str | None] = None
    deployment_handler_type: str = None
    deployment_pod_name: Optional[str | None] = None

    @validator("*", pre=True)
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v

    @field_validator("deployment_type")
    def validate_deployment_type(cls, value):
        if value not in ["continuous", "batch"]:
            raise ValueError("Invalid deployment type, must be continuous or batch")
        return value


# multi model service sub class
class MultiModelService(BaseWorkflow):
    workflow_model_name: list[str]
    workflow_model_version: list[str | PositiveInt]
    retrain: Optional[bool | None]


# client.set_registered_model_alias("generic_model", "challenger", result_generic.version)
# client.set_registered_model_tag("generic_model", "lattice_component", "ABC")
# client.set_registered_model_tag("generic_model", "lume_service", "false")
# client.set_registered_model_tag("generic_model", "lume_service_url", "")
# client.set_registered_model_tag("generic_model", "deployment_type", "continuous")
# client.set_registered_model_tag("generic_model", "multi_model_service", "false")
# client.set_registered_model_tag("generic_model", "retrain", "false")
# client.set_registered_model_tag("generic_model", "retrain_endpoint", "")
