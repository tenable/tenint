import pytest

from tenint.models import Configuration, Credential, Settings


@pytest.fixture
def config():
    class TestSettings(Settings):
        is_true: bool = True

    class TestCredential(Credential):
        name: str = "test"
        prefix: str = "test"
        slug: str = "test"
        description: str = "example"
        username: str
        password: str

    class TestConfiguration(Configuration):
        settings_model: Settings = TestSettings
        credential_models: list[Credential] = [TestCredential]
        defaults: Settings = TestSettings()

    return TestConfiguration()


def test_config(config):
    assert config.settings == {
        "properties": {
            "is_true": {"default": True, "title": "Is True", "type": "boolean"}
        },
        "title": "TestSettings",
        "type": "object",
        "additionalProperties": False,
    }
    assert config.credentials == [
        {
            "prefix": "test",
            "name": "test",
            "slug": "test",
            "definition": {
                "properties": {
                    "username": {"title": "Username", "type": "string"},
                    "password": {"title": "Password", "type": "string"},
                },
                "required": ["username", "password"],
                "title": "TestCredential",
                "type": "object",
            },
        }
    ]
