from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator
from pydantic.functional_validators import model_validator
from pydantic.networks import AnyHttpUrl, EmailStr


class TestingDependencies(BaseModel):
    testing: list[str]


class ProjectAuthor(BaseModel):
    name: str
    email: EmailStr


class TenintConnectorUrls(BaseModel):
    support: AnyHttpUrl


class Project(BaseModel):
    name: str
    description: str
    version: str
    authors: list[ProjectAuthor]
    urls: TenintConnectorUrls
    dependencies: list[str]
    optional_dependencies: Annotated[
        TestingDependencies, Field(alias="optional-dependencies")
    ]


class TenintConnectorTimeout(BaseModel):
    min: int = 3600
    default: int = 3600
    max: int = 86400


class TenintConnectorResources(BaseModel):
    disk: int = 1024
    memory: int = 1024
    cpu_cores: int = 1


class TenintConnector(BaseModel):
    title: str
    tags: list[str]
    schedule_types: list[Literal["hourly", "daily"]] = ["daily"]
    timeout: Annotated[TenintConnectorTimeout, Field(validate_default=True)] = {}
    resources: Annotated[TenintConnectorResources, Field(validate_default=True)] = {}


class Tenint(BaseModel):
    connector: TenintConnector


class Tools(BaseModel):
    tenint: Tenint


class PyProject(BaseModel):
    project: Project
    tool: Tools
