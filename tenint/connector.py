"""
Connector module

This module contains the Connector CLI wrapper and will act as the main interface point
for most integrators.
"""

import inspect
import json
import logging
import os
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

    def fetch_config(self, data: str) -> (BaseModel, int):
        """
        Fetch and validate the configuration from either the data string or the filepath
        and return the settings object to the caller.

        Args:
            data: JSON formatted string of the settings

        Returns:
            The pydantic settings model and the status code.
        """
        try:
            return self.settings(**json.loads(data)), 0
        except ValidationError as e:
            self.console.print(f"JSON String validation failed: {e}")
        except Exception as _:
            self.console.print_exception()
        return None, 2

    def callback(
        self, url: str | None, resp: dict, job_id: str | None, status_code: int
    ) -> None:
        """
        Initiate the callback response to the job scheduler

        Args:
            url: Callback url
            resp: Dictionary response of the job
            job_id: The Job UUID
            status_code: Job status
        """
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
        if job_id and url:
            requests.post(url, headers={"X-Job-ID": job_id}, json=payload, verify=False)
            logger.info(f"Called back to {url=} with {job_id=} and {payload=}")
        else:
            logger.warning("Did not initiate a callback!")
        logger.info(f"callback={payload}")

    def cmd_config(
        self, pretty: Annotated[bool, Option(help="Pretty format the response")] = False
    ):
        """
        Return the connector configuration
        """
        indent = 2 if pretty else None

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
            str,
            Option(
                "--json",
                "-j",
                envvar="CONFIG_JSON",
                help="The JSON config object as a string",
            ),
        ],
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
            LogLevel | None,
            Option(
                "--log-level",
                "-l",
                envvar="LOG_LEVEL",
                help="Sets the logging verbosity for the job",
                case_sensitive=False,
            ),
        ] = None,
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
        resp = None
        config, status_code = self.fetch_config(json_data)

        # Set the log level, using local before config and then ultimately setting the
        # log level to debug if nothing has been set.
        if log_level:
            lvl = log_level.upper()
        elif config:
            lvl = config.log_level
        else:
            lvl = "DEBUG"

        # Configure the logging handlers
        logging.basicConfig(
            level=lvl,
            format="%(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=[
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

        # Log the environment variables and configuration data
        self.log_env_vars()
        logger.info(f"Logging to {self.logfile}")
        logger.debug(f"Job {json_data=}")
        logger.info(f"Job config={config.model_dump_json() if config else None}")

        # Attempt to run the connector job and handle any errors that may be thrown
        # in a graceful way.
        try:
            if status_code == 0:
                resp = self.main(config=config, since=since)
        except Exception as _:
            logging.exception("Job run failed with error", stack_info=2)
            status_code = 1

        # Initiate the callback to the job management system.
        self.callback(
            url=callback_url, job_id=job_id, resp=resp, status_code=status_code
        )

        # Exit the connector with the status code from the runner.
        raise Exit(code=status_code)
