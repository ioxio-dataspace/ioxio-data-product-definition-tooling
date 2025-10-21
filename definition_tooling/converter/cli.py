from pathlib import Path

from typer import Argument, Exit, Option, Typer

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
    authorization_headers: bool = Option(
        False,
        help="Add headers for authorization ('Authorization' and "
        "'X-Authorization-Provider')",
    ),
    consent_headers: bool = Option(
        False,
        help="Add headers for consent ('X-Consent-Token')",
    ),
):
    should_fail_hook = convert_data_product_definitions(
        src, dest, authorization_headers, consent_headers
    )
    raise Exit(code=int(should_fail_hook))
