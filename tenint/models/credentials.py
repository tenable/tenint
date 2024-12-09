from typing import Any, Literal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, computed_field


def credential_schema(schema: dict[str, Any]) -> None:
    """
    Credential model schema adjustment.

    A simple function to remove the attributes that shouldn't be part of the UI schema
    from the schema itself.
    """
    for attr in ('prefix', 'name', 'slug', 'definition', 'description'):
        schema.get('properties', {}).pop(attr, None)


class Credential(BaseModel):
    """
    Credential base class
    """

    model_config = ConfigDict(json_schema_extra=credential_schema)
    description: str
    prefix: str
    name: str
    slug: str

    @computed_field
    @property
    def definition(self) -> dict[str, Any]:
        return self.model_json_schema()


class TenableVMCredential(Credential):
    """
    Tenable Vulnerability Management Credential
    """

    prefix: Literal['tio'] = 'tio'
    name: Literal['Tenable Vulnerability Management'] = (
        'Tenable Vulnerability Management'
    )
    slug: Literal['tvm'] = 'tvm'
    description: str = 'Tenable Vulnerability Management Credential'
    url: AnyHttpUrl = 'https://cloud.tenable.com'
    access_key: str
    secret_key: str


class TenableSCCredential(Credential):
    """
    Tenable Security Center Credential
    """

    prefix: Literal['tio'] = 'tsc'
    name: Literal['Tenable Security Center'] = 'Tenable Security Center'
    slug: Literal['tvm'] = 'tsc'
    description: str = 'Tenable Security Center Credential'
    url: AnyHttpUrl
    access_key: str
    secret_key: str
