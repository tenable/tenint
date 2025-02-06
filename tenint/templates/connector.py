import logging
from typing import Annotated

from pydantic import AnyHttpUrl, Field

from tenint import Connector, Credential, Settings


class TestCredential(Credential):
    prefix: str = "test"
    name: str = "Test Credential"
    slug: str = "test"
    api_key: Annotated[
        str,
        Field(title="API Key", description="Application API Key"),
    ]
    url: Annotated[
        AnyHttpUrl,
        Field(title="Application URL", description="Application URL"),
    ] = "https://httpbin.org/get"


class AppSettings(Settings):
    is_bool: Annotated[
        bool,
        Field(title="Yes?", description="An example boolean flag"),
    ] = True


log = logging.getLogger("test-connector")
connector = Connector(settings=AppSettings, credentials=[TestCredential])


@connector.job
def main(config: AppSettings, since: int | None = None) -> dict:
    log.debug("This is a debug test")
    log.info("this is an info test")
    log.warning("this is a warning")
    log.error("this is an error")
    print("hello world")
    return {"counts": {"assets": {"sent": 0}}}


if __name__ == "__main__":
    connector.app()
