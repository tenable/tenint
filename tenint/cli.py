import os
import subprocess
import tomllib
from pathlib import Path
from typing import Annotated

from rich.console import Console
from rich.panel import Panel
from typer import Option, Typer

from tenint.models.marketplace import MarketplaceConnector
from tenint.models.pyproject import PyProject

console = Console()
tmpl = Path(os.path.dirname(__file__)).joinpath("templates")
app = Typer()


@app.command("init")
def init_connector(
    path: Annotated[
        Path, Option(help="initialization path", dir_okay=True, file_okay=False)
    ] = Path("."),
):
    is_dirty = False
    for fn in ("pyproject.toml", "connector.py"):
        src = tmpl.joinpath(fn)
        dest = path.joinpath(fn)

        if dest.exists():
            console.print(
                f"[yellow bold]WARNING[/yellow bold]: skipped "
                f"existing [cyan]{dest}[/cyan] as it already exists"
            )
            is_dirty = True
        else:
            with src.open("rb") as sobj, dest.open("wb") as dobj:
                dobj.write(sobj.read())

    tests = path.joinpath("tests")
    if not tests.exists():
        tests.mkdir()
        src = tmpl.joinpath("test_connector.py")
        dest = tests.joinpath("test_connector.py")
        with dest.open("wb") as dobj, src.open("rb") as sobj:
            dobj.write(sobj.read())
    else:
        console.print(
            "[yellow bold]NOTE[/yellow bold]: skipped adding tests.  tests folder exists."
        )

    console.print(
        Panel(
            "Now that you have an initialized tenint connector, please review the "
            "files that have been created for your next steps.\n\n"
            "- [bold cyan]pyproject.toml[/bold cyan] contains the project "
            " requirements and is used to build the marketplace files\n"
            "- [bold cyan]connector.py[/bold cyan] is a sample connector "
            "to get you started.  It contains some example settings, a "
            "credential example, and a sample function.",
            title="[bold cyan]Tenable Integration Framework Connector[/bold cyan]",
        )
    )
    if is_dirty:
        console.print(
            Panel(
                "Could not initialize all of the files as some appeared to already "
                "exist.  Any files that previously existed were not modified.  "
                "Recommend manually reviewing your project to ensure everything "
                "looks correct.",
                title="[bold red]Dirty Environment Warning[/bold red]",
                style="yellow",
            )
        )


@app.command("build")
def build_connector(
    path: Annotated[Path, Option(help="connector code path")] = Path("."),
    platform: Annotated[str | None, Option(help="platform to build to")] = None,
    tag: Annotated[
        str | None,
        Option(help="Tag for the fimal image. defaults to the project name."),
    ] = None,
    cleanup: Annotated[
        bool | None, Option(help="auto-remove any generated build files?")
    ] = None,
):
    tmpldfile = tmpl.joinpath("Dockerfile")
    dockerfile = path.joinpath("Dockerfile")
    pyproject = path.joinpath("pyproject.toml")

    if not tag:
        with pyproject.open("rb") as pf:
            project = PyProject(**tomllib.load(pf))
            tag = project.project.name

    if not dockerfile.exists():
        with tmpldfile.open("rb") as src, dockerfile.open("wb") as dst:
            dst.write(src.read())
            cleanup = True if cleanup is None else cleanup

    builder = subprocess.Popen(
        ["docker", "build", "-t", tag, path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    for line in builder.stdout:
        console.out(line.decode("utf-8").strip("\n"))

    if cleanup:
        dockerfile.unlink()


@app.command("marketplace")
def gen_marketplace(
    image: Annotated[str, Option(..., help="Docker Image Name")] = None,
    icon: Annotated[
        str, Option(..., help="Icon Image URL")
    ] = "https://nourl.example/logo.svg",
    path: Annotated[Path, Option(help="connector code path")] = Path("."),
    output: Annotated[Path, Option(help="output marketplace json file")] = None,
):
    pyproject_file = path.joinpath("pyproject.toml")
    with pyproject_file.open("rb") as fobj:
        project = PyProject(**tomllib.load(fobj))

    if not image:
        image = project.project.name

    mpfile = path.joinpath("marketplace-object.json")
    mp = MarketplaceConnector.load_from_pyproject(
        filename=project, image_url=image, icon_url=icon
    ).model_dump(mode="json")
    console.print(mp)
    if output:
        with mpfile.open("w", encoding="utf-8") as fobj:
            fobj.write(mp.model_dump_json())
