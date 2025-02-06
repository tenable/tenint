from typing import Annotated, Any, Literal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, SecretStr, computed_field


def credential_schema(schema: dict[str, Any]) -> None:
    """
    Credential model schema adjustment.

    A simple function to remove the attributes that shouldn't be part of the UI schema
    from the schema itself.
    """
    for attr in ("prefix", "name", "slug", "definition", "description"):
        schema.get("properties", {}).pop(attr, None)


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

    @classmethod
    def env_secrets(cls) -> list[str]:
        resp = []
        schema = cls.model_json_schema()
        prefix = cls.model_fields["prefix"].default
        for name, props in schema["properties"].items():
            if props.get("format") == "password":
                resp.append(f"{prefix}_{name}".upper())
        return resp


class TenableCloudCredential(Credential):
    """
    Tenable Cloud Credential
    """

    prefix: Literal["tio"] = "tio"
    name: Literal["Tenable Cloud"] = "Tenable Cloud"
    slug: Literal["tvm"] = "tvm"
    description: str = "Tenable Cloud Credential"
    url: Annotated[
        AnyHttpUrl,
        Field(
            title="Cloud URL",
            description="Only needs to be modified when interacting with a FedRAMP cloud instance",
        ),
    ] = "https://cloud.tenable.com"
    access_key: Annotated[
        str,
        Field(title="API Access Key", description="Tenable Cloud API Access Key"),
    ]
    secret_key: Annotated[
        SecretStr,
        Field(title="API Secret Key", description="Tenable Cloud API Secret Key"),
    ]


class TenableSCCredential(Credential):
    """
    Tenable Security Center Credential
    """

    prefix: Literal["tsc"] = "tsc"
    name: Literal["Tenable Security Center"] = "Tenable Security Center"
    slug: Literal["tsc"] = "tsc"
    description: str = "Tenable Security Center Credential"
    url: Annotated[
        AnyHttpUrl,
        Field(title="Host URL", description="Security Center Application URL"),
    ]
    access_key: Annotated[
        str,
        Field(title="API Access Key", description="Security Center API Access Key"),
    ]
    secret_key: Annotated[
        SecretStr,
        Field(title="API Secret Key", description="Security Center API Secret Key"),
    ]
