import asyncio
import logging
import os
import subprocess
import sys
from typing import Annotated

import typer
from rich.console import Console

from gaf_guard.clients.benchmark import run_benchmark
from gaf_guard.serve import start_server
from gaf_guard.toolkit.logging import configure_logger


httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.ERROR)

LOGGER = configure_logger(__name__)

app = typer.Typer()
console = Console()


@app.callback()
def main() -> None:
    """
    GAF Guard Redirect Server
    """


@app.command()
def benchmark(
    ground_trial: Annotated[
        str,
        typer.Argument(
            help="Please enter ground truth file path.",
            rich_help_panel="Ground Truth Trial",
        ),
    ],
    host: Annotated[
        str,
        typer.Argument(help="Please enter GAF Guard Host.", rich_help_panel="Hostname"),
    ] = "localhost",
    port: Annotated[
        int,
        typer.Argument(help="Please enter GAF Guard Port.", rich_help_panel="Port"),
    ] = 8000,
):
    asyncio.run(run_benchmark(ground_trial, host, port))


@app.command()
def serve(config_file):
    start_server(config_file)


@app.command()
def client(
    client: Annotated[
        str,
        typer.Argument(
            help="Please enter GAF Guard Client type",
            rich_help_panel="GAF Guard Client",
        ),
    ],
    host: Annotated[
        str,
        typer.Argument(help="Please enter GAF Guard Host.", rich_help_panel="Hostname"),
    ] = "localhost",
    port: Annotated[
        int,
        typer.Argument(help="Please enter GAF Guard Port.", rich_help_panel="Port"),
    ] = 8000,
):
    os.system("clear")
    console.rule(f"[bold blue]Launching GAF Guard {client.title()} Client[/bold blue]")
    try:
        if client == "streamlit":
            process = subprocess.Popen(
                ["streamlit", "run", f"src/gaf_guard/clients/{client}.py"],
                stderr=subprocess.STDOUT,
                text=True,
            )
        elif client == "cli":
            process = subprocess.Popen(
                [
                    "python",
                    f"src/gaf_guard/clients/{client}.py",
                    "--host",
                    host,
                    "--port",
                    str(port),
                ],
                stderr=subprocess.STDOUT,
                text=True,
            )

        # Wait for the process to fully terminate and get the return code
        return_code = process.wait()
        return return_code
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}. Error:")
        print(e.stderr)


# if __name__ == "__main__":
#     app()
