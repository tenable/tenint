import json
import logging
from typing import Any

import pytest
import responses
from responses import matchers
from rich.console import Console
from typer import Typer
from typer.testing import CliRunner

from tenint.connector import ConfigurationError, Connector, Settings

runner = CliRunner()


@pytest.fixture
def AppSettings():
    class AppSettings(Settings):
        is_bool: bool = True

    return AppSettings


@pytest.fixture
def main():
    def main(config: dict[str, Any], since: int | None = None):
        log = logging.getLogger("main-test")
        log.debug("This is a debug test")
        log.info("This is an info test")
        log.error("This is an error test")
        print("hello world")

    return main


def test_connector_init(AppSettings):
    connector = Connector(settings=AppSettings)
    assert isinstance(connector.app, Typer)
    assert isinstance(connector.console, Console)
    assert connector.settings == AppSettings
    assert connector.credentials == []
    assert connector.defaults == {"is_bool": True}


def test_connector_fetch_config_string_data(AppSettings):
    connector = Connector(settings=AppSettings)
    assert connector.fetch_config(data='{"is_bool": true}')


def test_connector_fetch_config_json_file(AppSettings, tmp_path):
    fn = tmp_path.joinpath("example.json")
    fn.write_text('{"is_bool": true}')
    connector = Connector(settings=AppSettings)
    assert connector.fetch_config(fn=fn) == AppSettings(is_bool=True)


def test_connector_fetch_config_toml_file(AppSettings, tmp_path):
    fn = tmp_path.joinpath("example.toml")
    fn.write_text("is_bool = true")
    connector = Connector(settings=AppSettings)
    assert connector.fetch_config(fn=fn) == AppSettings(is_bool=True)


def test_connector_fetch_config_failure(AppSettings):
    connector = Connector(settings=AppSettings)
    with pytest.raises(ConfigurationError):
        connector.fetch_config()


def test_connector_config_cli(AppSettings, main):
    test_resp = {
        "settings": {
            "additionalProperties": False,
            "properties": {
                "is_bool": {"default": True, "title": "Is Bool", "type": "boolean"}
            },
            "title": "AppSettings",
            "type": "object",
        },
        "credentials": [],
        "defaults": {"is_bool": True},
    }
    connector = Connector(settings=AppSettings)
    result = runner.invoke(connector.app, ["config"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == test_resp


def test_connector_job_decorator(AppSettings, main):
    connector = Connector(settings=AppSettings)
    connector.job(main)
    assert main == connector.main


def test_connector_validation(AppSettings):
    connector = Connector(settings=AppSettings)
    result = runner.invoke(connector.app, ["validate"])
    assert "Not yet implemented" in result.stdout


def test_connector_run(AppSettings, main, caplog):
    connector = Connector(settings=AppSettings)
    connector.job(main)
    with caplog.at_level(logging.DEBUG):
        result = runner.invoke(connector.app, ["run", "-j", '{"is_bool": true}'])
        assert result.exit_code == 0
        assert "Job config" in caplog.text
        assert "EnvVar" in caplog.text
        assert "hello world" in result.stdout
        assert "This is a debug test" in caplog.text
        assert "This is an info test" in caplog.text
        assert "This is an error test" in caplog.text
        assert "Job response format is invalid" in caplog.text
        assert "Did not initiate a callback!" in caplog.text
        assert "callback={" in result.stdout


def test_connector_run_config_fail(AppSettings, main):
    connector = Connector(settings=AppSettings)
    connector.job(main)
    result = runner.invoke(connector.app, ["run", "-j", '{"this": "failure"}'])
    assert result.exit_code == 2


def test_connector_run_fail(AppSettings, caplog):
    connector = Connector(settings=AppSettings)

    @connector.job
    def failmain(config: dict, since: None = None):
        raise Exception("I have failed")

    with caplog.at_level(logging.INFO):
        result = runner.invoke(connector.app, ["run", "-j", '{"is_bool": true}'])
        assert result.exit_code == 1
        assert "I have failed" in result.stdout


@responses.activate
def test_connector_callback(AppSettings, main, caplog):
    responses.post(
        "http://callback-url.local/callback",
        match=[matchers.header_matcher({"X-Job-ID": "abcdef"})],
    )
    connector = Connector(settings=AppSettings)
    connector.job(main)

    with caplog.at_level(logging.INFO):
        result = runner.invoke(
            connector.app,
            [
                "run",
                "-j",
                '{"is_bool": true}',
                "-J",
                "abcdef",
                "-c",
                "http://callback-url.local/callback",
            ],
        )
        assert result.exit_code == 0
        assert "Called back" in caplog.text
        assert "callback_url='http://callback-url.local/callback'" in caplog.text
        assert "job_id='abcdef'" in caplog.text
