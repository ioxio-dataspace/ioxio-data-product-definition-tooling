from typing import Any, List, Optional

from rich import print
from rich.console import Console
from rich.table import Table


def print_error(msg):
    print(f"[red]{msg}[/red]")


def print_success(msg):
    print(f"[green]{msg}[/green]")


def print_table(headers: List[str], rows: List[List[Any]], style: Optional[str] = None):
    console = Console()
    table = Table(*headers, style=style)
    for row in rows:
        table.add_row(*[str(c) for c in row])
    console.print(table)
