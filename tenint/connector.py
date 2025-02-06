"""
Connector module

This module contains the Connector CLI wrapper and will act as the main interface point
for most integrators.
"""

import inspect
import json
import logging
import os
import tomllib
from enum import Enum
from pathlib import Path
from typing import Annotated, Callable

import requests
from pydantic import BaseModel, ValidationError
from rich import print, print_json
from rich.console import Console
from rich.logging import RichHandler
from typer import Exit, Option, Typer
from typer.main import get_command_name

from .models.callback import CallbackResponse
from .models.configuration import Configuration, Settings
from .models.credentials import Credential

logger = logging.getLogger("tenint.connector")


class ConfigurationError(Exception):
    pass


class LogLevel(str, Enum):
    notset = "notset"
    debug = "debug"
    info = "info"
    warning = "warning"
    error = "error"
    critical = "critical"


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
        self.logfile = Path("job.log").absolute()
        self.console = Console(file=self.logfile.open("a", encoding="utf-8"), width=135)
        self.app = Typer(add_completion=False)
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
            if method.startswith("cmd_"):
                name = get_command_name(method.removeprefix("cmd_"))
                self.app.command(name=name)(func)

    def job(self, func: Callable) -> Callable:
        """
        The Connector job decorator.
        """
        self.main = func
        return func

    def log_env_vars(self) -> None:
        clean = []

        # Build the hidden list
        for cred in self.credentials:
            clean += cred.env_secrets()

        for key, value in os.environ.items():
            if key in clean:
                value = "{{ HIDDEN }}"
            logger.debug(f'EnvVar {key}="{value}"')

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
        elif fn and fn.is_file() and fn.suffix.lower() in [".json", ".jsn"]:
            with fn.open("r", encoding="utf-8") as fobj:
                settings = self.settings(**json.load(fobj))

        # If the file passed has a TOML suffix, we will process as a toml file through
        # tomllib.
        elif fn and fn.is_file() and fn.suffix.lower() in [".toml", ".tml"]:
            with fn.open("rb") as fobj:
                settings = self.settings(**tomllib.load(fobj))

        # If we processed anything, then return the settings object, otherwise raise a
        # ConfigurationError
        if settings:
            logger.debug(f"Job config={settings.model_dump(mode='json')}")
            return settings
        raise ConfigurationError("No valid configurations passed.")

    def cmd_config(
        self, pretty: Annotated[bool, Option(help="Pretty format the response")] = False
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

        print_json(
            Config(defaults=self.defaults).model_dump_json(
                include=["settings", "credentials", "defaults"]
            ),
            indent=indent,
        )

    def cmd_validate(self):
        """
        Validate the connector settings and credentials
        """
        print("Not yet implemented")

    def cmd_run(
        self,
        json_data: Annotated[
            str | None,
            Option(
                "--json",
                "-j",
                envvar="CONFIG_JSON",
                help="The JSON config object as a string",
            ),
        ] = None,
        filename: Annotated[
            Path | None,
            Option(
                "--filename",
                "-f",
                envvar="CONFIG_FILENAME",
                help="Filename of either a json or toml file containing the job config",
            ),
        ] = None,
        job_id: Annotated[
            str | None,
            Option(
                "--job-id",
                "-J",
                envvar="JOB_ID",
                help="The unique job id of this invocation",
            ),
        ] = None,
        callback_url: Annotated[
            str | None,
            Option(
                "--callback",
                "-c",
                envvar="CALLBACK_URL",
                help="The URL the connector should call back to when it completes",
            ),
        ] = None,
        log_level: Annotated[
            LogLevel,
            Option(
                "--log-level",
                "-l",
                envvar="LOG_LEVEL",
                help="Sets the logging verbosity for the job",
                case_sensitive=False,
            ),
        ] = LogLevel.info,
        since: Annotated[
            int | None,
            Option(
                "--since",
                "-s",
                envvar="SINCE",
                help="When did the last successful run start?",
            ),
        ] = None,
    ):
        """
        Invoke the connector
        """
        logging.basicConfig(
            level=log_level.upper(),
            # format="%(asctime) %(name)s(%(filename)s:%(lineno)d): %(message)s",
            format="%(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=[
                # logging.FileHandler("job.log"),
                RichHandler(
                    console=self.console,
                    show_path=False,
                    rich_tracebacks=True,
                    tracebacks_show_locals=True,
                    omit_repeated_times=False,
                ),
                logging.StreamHandler(),
            ],
        )
        self.log_env_vars()
        logger.info(f"Logging to {self.logfile}")
        status_code = 0
        resp = None

        # Attempt to run the connector job and handle any errors that may be thrown
        # in a graceful way.
        try:
            config = self.fetch_config(json_data, filename)
            resp = self.main(config=config, since=since)
        except (ValidationError, ConfigurationError) as e:
            logging.error(f"Invalid configuration presented: {e}")
            status_code = 2
        except Exception as _:
            logging.exception("Job run failed with error", stack_info=2)
            status_code = 1

        # Set the Callback payload to the job response if the response is a dictionary
        try:
            payload = CallbackResponse(exit_code=status_code, **resp).model_dump(
                mode="json"
            )
        except (ValidationError, TypeError) as _:
            logger.error(f"Job response format is invalid: {resp=}")
            payload = CallbackResponse(exit_code=status_code).model_dump(mode="json")

        # If a callback and a job id have been set, then we will initiate a callback
        # to the job manager with the response payload of the job to inform the manager
        # that we have finished.
        if job_id and callback_url:
            requests.post(
                callback_url,
                headers={"X-Job-ID": job_id},
                json=payload,
                verify=False,
            )
            logger.info(f"Called back to {callback_url=} with {job_id=} and {payload=}")
        else:
            logger.warning("Did not initiate a callback!")
        logger.info(f"callback={payload}")

        # Exit the connector with the status code from the runner.
        raise Exit(code=status_code)
