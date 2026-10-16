"""Command-line interface for imgw-meteo.

Imports of typer/rich are lazy so that an API-only install (without the [cli]
extra) never requires them. Running the command without the extra prints a
clear install hint.
"""

import sys

_CLI_HINT = "CLI extras not installed — run: pip install imgw-meteo[cli]"


def _require_cli():
    try:
        import typer  # noqa: F401
    except ImportError:
        print(_CLI_HINT, file=sys.stderr)
        raise SystemExit(1) from None


def build_app():
    _require_cli()
    import typer
    from rich.console import Console
    from rich.table import Table

    from . import IMGWClient

    app = typer.Typer(add_completion=False, help="IMGW meteo data tool.")
    console = Console()

    @app.command()
    def stations(name: str = typer.Option(None, help="Filter by station name.")) -> None:
        """List stations (optionally filtered by name)."""
        client = IMGWClient()
        reg = client.stations()
        results = reg.search(name) if name else reg.all()
        table = Table("Code", "Name", "Code5")
        for s in results[:200]:
            table.add_row(s.code, s.name, s.code5)
        console.print(table)
        console.print(f"[dim]{len(results)} station(s)[/dim]")

    @app.command()
    def years(
        freq: str = typer.Option("daily", help="daily|monthly|term"),
        type: str = typer.Option("synop", help="synop|klimat|opad"),
    ) -> None:
        """List available years for a frequency/station type."""
        client = IMGWClient()
        for y in client.available_years(freq, type):
            console.print(y)

    @app.command()
    def fetch(
        freq: str = typer.Option("daily", help="daily|monthly|term"),
        type: str = typer.Option("klimat", help="synop|klimat|opad"),
        year: int = typer.Option(...),
        month: int = typer.Option(None),
        station: str = typer.Option(None),
        output: str = typer.Option(None, help="Write to .csv/.parquet instead of stdout."),
    ) -> None:
        """Fetch and standardize data for a selection."""
        client = IMGWClient()
        ds = client.select(
            frequency=freq,
            station_type=type,
            years=year,
            months=month,
            stations=station,
        )
        if output:
            path = ds.export(output)
            console.print(f"[green]wrote[/green] {path}")
        else:
            df = ds.get_dataframe()
            console.print(df.head(20).to_string())
            console.print(f"[dim]{len(df)} rows x {df.shape[1]} cols[/dim]")

    return app


def main() -> None:
    app = build_app()
    app()


if __name__ == "__main__":
    main()
