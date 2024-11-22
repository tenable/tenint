"""
Connector module

This module contains the Connector CLI wrapper and will act as the main interface point
for most integrators.
"""

import inspect
import json
import logging
import tomllib
from enum import Enum
from pathlib import Path
from typing import Annotated, Callable

import requests
from pydantic import BaseModel, ValidationError
from rich.console import Console
from rich.logging import RichHandler
from typer import Exit, Option, Typer
from typer.main import get_command_name

from .models.configuration import Configuration, Settings
from .models.credentials import Credential


class ConfigurationError(Exception):
    pass


class LogLevel(str, Enum):
    notset = 'notset'
    debug = 'debug'
    info = 'info'
    warning = 'warning'
    error = 'error'
    critical = 'critical'


class Connector:
    """
    The Connector class handles wrapping the connector code into a compliant connector
    commandline for use in integrating into the tenable integration framework.

    Args:
        settings:
            A pydantic BaseModel class describing how the connector settings.
        credentials:
            A list of Credential classes detailing the required credentials needed to
            run the connector.
    """

    app: Typer
    config: Configuration

    def __init__(
        self,
        settings: type[Settings],
        defaults: Settings | None = None,
        credentials: list[type[Credential]] | None = None,
    ):
        self.app = Typer(add_completion=False)
        self.console = Console()

        self.settings = settings
        self.defaults = (
            defaults if defaults else settings.model_construct().model_dump()
        )
        self.credentials = credentials if credentials else []

        # Iterate through the methods on the class and construct the command-line
        # commands using the method name.  We will only want to inject commands into
        # typer that start with the cmd_ prefix.  NOTE this code has been shamelessly
        # ripped from an issue in the Typer GH repo:
        #
        # https://github.com/fastapi/typer/issues/309#issuecomment-1937836010
        #
        # e.g. cmd_config -> config
        for method, func in inspect.getmembers(self, predicate=inspect.ismethod):
            if method.startswith('cmd_'):
                name = get_command_name(method.removeprefix('cmd_'))
                self.app.command(name=name)(func)

    def job(self, func: Callable) -> Callable:
        """
        The Connector job decorator.
        """
        self.main = func
        return func

    def fetch_config(
        self,
        data: str | None = None,
        fn: Path | None = None,
    ) -> BaseModel:
        """
        Fetch and validate the configuration from either the data string or the filepath
        and return the settings object to the caller.

        Args:
            data:
                The string object of the
        """
        settings = None

        # If a string object is passed, we will handle that first.
        if data:
            settings = self.settings(**json.loads(data))

        # If a file has been passed in instead an the suffix appears to be a JSON
        # suffix, then we will assume a JSON file and handle accordingly.
        elif fn and fn.is_file() and fn.suffix.lower() in ['.json', '.jsn']:
            with fn.open('r', encoding='utf-8') as fobj:
                settings = self.settings(**json.load(fobj))

        # If the file passed has a TOML suffix, we will process as a toml file through
        # tomllib.
        elif fn and fn.is_file() and fn.suffix.lower() in ['.toml', '.tml']:
            with fn.open('rb') as fobj:
                settings = self.settings(**tomllib.load(fobj))

        # If we processed anything, then return the settings object, otherwise raise a
        # ConfigurationError
        if settings:
            return settings
        raise ConfigurationError('No valid configurations passed.')

    def cmd_config(
        self, pretty: Annotated[bool, Option(help='Pretty format the response')] = False
    ):
        """
        Return the connector configuration
        """
        indent = 2
        if not pretty:
            indent = None

        class Config(Configuration):
            settings_model: type[Settings] = self.settings
            credential_models: list[type[Credential]] = self.credentials

        self.console.print_json(
            Config(defaults=self.defaults).model_dump_json(
                include=['settings', 'credentials', 'defaults']
            ),
            indent=indent,
        )

    def cmd_validate(self):
        """
        Validate the connector settings and credentials
        """
        self.console.print('Not yet implemented')

    def cmd_run(
        self,
        json_data: Annotated[
            str | None,
            Option(
                '--json',
                '-j',
                envvar='CONFIG_JSON',
                help='The JSON config object as a string',
            ),
        ] = None,
        filename: Annotated[
            Path | None,
            Option(
                '--filename',
                '-f',
                envvar='CONFIG_FILENAME',
                help='Filename of either a json or toml file containing the job config',
            ),
        ] = None,
        job_id: Annotated[
            str | None,
            Option(
                '--job-id',
                '-J',
                envvar='JOB_ID',
                help='The unique job id of this invocation',
            ),
        ] = None,
        callback_url: Annotated[
            str | None,
            Option(
                '--callback',
                '-c',
                envvar='CALLBACK_URL',
                help='The URL the connector should call back to when it completes',
            ),
        ] = None,
        log_level: Annotated[
            LogLevel,
            Option(
                '--log-level',
                '-l',
                envvar='LOG_LEVEL',
                help='Sets the logging verbosity for the job',
                case_sensitive=False,
            ),
        ] = LogLevel.info,
    ):
        """
        Invoke the connector
        """
        logging.basicConfig(
            level=log_level.upper(),
            format='%(asctime)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[RichHandler(console=self.console, rich_tracebacks=True)],
        )
        status_code = 0

        try:
            config = self.fetch_config(json_data, filename)
            self.main(config=config)
        except (ValidationError, ConfigurationError) as exc:
            self.console.print(exc)
            status_code = 2
        except Exception as _:
            self.console.print_exception()
            status_code = 1

        if job_id and callback_url:
            requests.post(callback_url, headers={'X-Job-ID': job_id})
            self.console.log(f'Called back to {callback_url=} with {job_id=}')
        else:
            self.console.print('Did not initiate a callback!', style='bold orange1')
        raise Exit(code=status_code)
