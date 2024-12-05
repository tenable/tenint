from typing import Annotated

from pydantic import BaseModel, Field
from pydantic.networks import AnyHttpUrl, EmailStr


class TestingDependencies(BaseModel):
    testing: list[str]


class ProjectAuthor(BaseModel):
    name: str
    email: EmailStr


class TenintConnectorUrls(BaseModel):
    repository: AnyHttpUrl
    logo: AnyHttpUrl
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


class TenintImages(BaseModel):
    amd64: str
    arm64: str | None = None


class TenintConnector(BaseModel):
    title: str
    tags: list[str]
    timeout: int = 3600
    images: TenintImages


class Tenint(BaseModel):
    connector: TenintConnector


class Tools(BaseModel):
    tenint: Tenint


class PyProject(BaseModel):
    project: Project
    tool: Tools
