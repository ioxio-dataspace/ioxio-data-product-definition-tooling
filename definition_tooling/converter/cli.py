from pathlib import Path

from typer import Argument, Exit, Typer

from definition_tooling.converter import convert_data_product_definitions

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
    should_fail_hook = convert_data_product_definitions(src, dest)
    raise Exit(code=int(should_fail_hook))
