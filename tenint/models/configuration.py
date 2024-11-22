from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from .credentials import Credential


class Settings(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Configuration(BaseModel):
    settings_model: type[Settings] = Field(exclude=True)
    credential_models: list[type[Credential]] = Field(exclude=True, default=[])
    defaults: dict

    @computed_field
    @property
    def settings(self) -> dict[str, Any]:
        return self.settings_model.model_json_schema()

    @computed_field
    @property
    def credentials(self) -> list[dict[str, Any]]:
        return [
            C.model_construct().model_dump(
                mode='json',
                include=['name', 'slug', 'prefix', 'definition'],
            )
            for C in self.credential_models
        ]
