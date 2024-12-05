from __future__ import annotations

import tomllib
from pathlib import Path

from pydantic import AnyHttpUrl, BaseModel, EmailStr, Field

from .pyproject import PyProject


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

    @classmethod
    def load_from_pyproject(
        cls, filename: PyProject | Path | str
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
            icon_url=obj.project.urls.logo,
            image_url=obj.tool.tenint.connector.images.amd64,
            marketplace_tag=obj.project.version,
            connector_owner=obj.project.authors[0].name,
            support_contact=obj.project.authors[0].email,
            tags=obj.tool.tenint.connector.tags,
        )
