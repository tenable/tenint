from tenint.models.credentials import (
    Credential,
    TenableCloudCredential,
    TenableSCCredential,
)


def test_base_credential_model():
    class TestCredential(Credential):
        prefix: str = "test"
        name: str = "Test Credential"
        slug: str = "test"
        description: str = "Example"
        username: str
        password: str
        url: str = "https://test.url.local"

    cred = TestCredential(username="user", password="pass")
    assert cred.prefix == "test"
    assert cred.name == "Test Credential"
    assert cred.slug == "test"
    assert cred.username == "user"
    assert cred.password == "pass"
    assert cred.description == "Example"
    assert cred.url == "https://test.url.local"
    assert cred.definition == {
        "properties": {
            "password": {"title": "Password", "type": "string"},
            "url": {
                "default": "https://test.url.local",
                "title": "Url",
                "type": "string",
            },
            "username": {"title": "Username", "type": "string"},
        },
        "required": ["username", "password"],
        "title": "TestCredential",
        "type": "object",
    }
    assert cred.model_json_schema() == {
        "properties": {
            "password": {"title": "Password", "type": "string"},
            "url": {
                "default": "https://test.url.local",
                "title": "Url",
                "type": "string",
            },
            "username": {"title": "Username", "type": "string"},
        },
        "required": ["username", "password"],
        "title": "TestCredential",
        "type": "object",
    }


def test_tenable_cloud_cred():
    assert TenableCloudCredential.model_fields["prefix"].default == "tio"
    assert TenableCloudCredential.model_fields["name"].default == "Tenable Cloud"
    assert TenableCloudCredential.model_fields["slug"].default == "tvm"
    assert TenableCloudCredential.env_secrets() == ["TIO_SECRET_KEY"]


def test_tenable_sc_cred():
    assert TenableSCCredential.model_fields["prefix"].default == "tsc"
    assert TenableSCCredential.model_fields["name"].default == "Tenable Security Center"
    assert TenableSCCredential.model_fields["slug"].default == "tsc"
    assert TenableSCCredential.env_secrets() == ["TSC_SECRET_KEY"]
