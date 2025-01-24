from typing import Annotated

from pydantic import BaseModel, Field
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


class TenintConnector(BaseModel):
    title: str
    tags: list[str]
    timeout: int = 3600


class Tenint(BaseModel):
    connector: TenintConnector


class Tools(BaseModel):
    tenint: Tenint


class PyProject(BaseModel):
    project: Project
    tool: Tools
