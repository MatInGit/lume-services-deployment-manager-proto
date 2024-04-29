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
    retrain: Optional[bool | None] = False
    retrain_endpoint: Optional[AnyUrl | None] = None
    lattice_component: Optional[str] = None
    lume_service: Optional[bool | None] = False
    lume_service_url: Optional[AnyUrl | None] = None
    maintainer: Optional[str | None] = None
    deplyment_status: Optional[str | None] = None
    deployment_handler_type: str = None
    deployment_pod_name: Optional[str | None] = None
    data_source: Optional[str | None] = None
    deployment_terminate: Optional[bool | None] = False

    @validator("*", pre=True)
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v

    @field_validator("deployment_type")
    def validate_deployment_type(cls, value):
        if value not in ["continuous", "batch", "flow", "prod"]:
            raise ValueError(
                "Invalid deployment type, must be continuous, flow or batch"
            )
        return value


class ExampleChildWorkflow(BaseWorkflow):
    lattice_component: str
    lume_service: bool
    lume_service_url: AnyUrl
    data_source: str
