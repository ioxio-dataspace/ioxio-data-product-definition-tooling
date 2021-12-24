from pathlib import Path

from typer import Argument, Typer

from converter import convert_data_product_definitions

cli = Typer()


@cli.command()
def convert_definitions(
    src: Path = Argument(
        ...,
        help="Path to python sources of definitions",
        dir_okay=True,
        file_okay=False,
        exists=True,
    ),
    dest: Path = Argument(
        ...,
        help="Path to definitions output",
        dir_okay=True,
        file_okay=False,
        exists=True,
    ),
):
    convert_data_product_definitions(src, dest)
