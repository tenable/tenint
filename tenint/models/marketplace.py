from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, EmailStr

from .pyproject import PyProject


class MarketplaceResources(BaseModel):
    disk: int
    memory: int
    cpu_cores: int


class MarketplaceTimeout(BaseModel):
    min: int
    default: int
    max: int


class MarketplaceConnector(BaseModel):
    name: str
    slug: str
    description: str
    icon_url: AnyHttpUrl
    image_url: str
    marketplace_tag: str
    connector_owner: str
    support_contact: EmailStr
    tags: list[str]
    schedule_types: list[Literal["hourly", "daily"]]
    resources: MarketplaceResources
    timeout: MarketplaceTimeout

    @classmethod
    def load_from_pyproject(
        cls,
        filename: PyProject | Path | str,
        image_url: str,
        icon_url: str,
    ) -> MarketplaceConnector:
        """
        Builds the marketplace object off of the PyProject file.

        Args:
            filename:
                The filename of the pyproject.toml file.

        Returns:
            Marketplace:
                The marketplace object.

        Example:

            >>> marketplace = Marketplace.load_from_pyproject('pyproject.toml')
        """
        if isinstance(filename, PyProject):
            obj = filename
        else:
            if isinstance(filename, str):
                filename = Path(filename)
            with filename.open("rb") as fobj:
                obj = PyProject(**tomllib.load(fobj))
        return cls(
            name=obj.tool.tenint.connector.title,
            slug=obj.project.name,
            description=obj.project.description,
            icon_url=icon_url,
            image_url=image_url,
            timeout=obj.tool.tenint.connector.timeout.model_dump(),
            resources=obj.tool.tenint.connector.resources.model_dump(),
            schedule_types=obj.tool.tenint.connector.schedule_types,
            marketplace_tag=obj.project.version,
            connector_owner=obj.project.authors[0].name,
            support_contact=obj.project.authors[0].email,
            tags=obj.tool.tenint.connector.tags,
        )
