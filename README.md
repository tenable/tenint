# Tenable Integrations Framework Connector SDK (Tenint)

The goal of the tenint SDK is to provide a simple and reliable way to build the
common framework needed to build the connector so that the framework can load & run
the connector code.

Currently the code connector code is in a working state, however the commandline
interface is still being actively developed.  Currently supported with the `tenint`
command is the following commands:

```bash
# To initialize a project with an example connector.py & pyproject.toml file.
tenint init 

# To build the connector image for local launching within docker
tenint build
```

## Basics of a connector

Connectors require at a minimum a `Settings` object, the `Connector` object loaded
and pointed to you're main handler, and the app launcher in order to load the
interface.

At the absolute minimum, you would need the following:

```python
from tenint import Connector, Settings


class AppSettings(Settings):
	value: str


connector = Connector(settings=AppSettings)


@connector.job
def run_me(config: AppSettings):
	print(f"Hello World!  Launched with {config.value}")


if __name__ == '__main__':
	connector.app()
```

### Settings

The Settings class is a pydantic model that you can setup with the settings that you
wish to expose to the user within the TIF interface.  It will use the model to
generate a JSONSchema defintion that is used to paint that page.

## Running you code locally (no docker)

To run the code above, there are two commands exposed, `config` and `run`

```bash
python connector.py config

python connector.py run -j "{"value": "some string"}"
```
