# This file is autogenerated.
# To change this file you should edit assets/configuration/spec.yaml and then run the following commands:
#     ddev -x validate config -s <INTEGRATION_NAME>
#     ddev -x validate models -s <INTEGRATION_NAME>

from __future__ import annotations

from typing import Optional, Sequence

from pydantic import BaseModel, root_validator, validator

from datadog_checks.base.utils.functions import identity
from datadog_checks.base.utils.models import validation

from . import defaults, validators


class MetricPatterns(BaseModel):
    class Config:
        allow_mutation = False

    exclude: Optional[Sequence[str]]
    include: Optional[Sequence[str]]


class InstanceConfig(BaseModel):
    class Config:
        allow_mutation = False

    boomi_account_id: Optional[str]
    boomi_api_gateway_install_dir: Optional[str]
    boomi_api_gateway_node_id: Optional[str]
    boomi_api_token: Optional[str]
    boomi_api_url: Optional[str]
    boomi_api_userid: Optional[str]
    boomi_atom_or_molecule_install_dir: str
    boomi_molecule_node_id: Optional[str]
    dd_api_key: str
    disable_generic_tags: Optional[bool]
    empty_default_hostname: Optional[bool]
    metric_patterns: Optional[MetricPatterns]
    min_boomi_api_interval: int
    min_collection_interval: Optional[float]
    seconds_of_lag: int
    service: Optional[str]
    tags: Optional[Sequence[str]]

    @root_validator(pre=True)
    def _initial_validation(cls, values):
        return validation.core.initialize_config(getattr(validators, 'initialize_instance', identity)(values))

    @validator('*', pre=True, always=True)
    def _ensure_defaults(cls, v, field):
        if v is not None or field.required:
            return v

        return getattr(defaults, f'instance_{field.name}')(field, v)

    @validator('*')
    def _run_validations(cls, v, field):
        if not v:
            return v

        return getattr(validators, f'instance_{field.name}', identity)(v, field=field)

    @root_validator(pre=False)
    def _final_validation(cls, values):
        return validation.core.finalize_config(getattr(validators, 'finalize_instance', identity)(values))