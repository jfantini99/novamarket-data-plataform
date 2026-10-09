from datetime import date
from typing import Annotated

import typer

from novamarket.datagen.config import INCIDENT_SCENARIOS, SCALES

app = typer.Typer(help="NovaMarket Data Engineering Lab CLI", no_args_is_help=True)
data_app = typer.Typer(help="Geração e carga de dados sintéticos", no_args_is_help=True)
app.add_typer(data_app, name="data")


@app.callback()
def main() -> None:
    """NovaMarket Data Engineering Lab."""


@app.command()
def version() -> None:
    """Mostra a versão da CLI."""
    from novamarket import __version__

    typer.echo(__version__)


@data_app.command("generate")
def data_generate(
    scale: Annotated[str, typer.Option(help=f"Escala: {', '.join(SCALES)}")] = "small",
    seed: Annotated[int, typer.Option(help="Mesma seed gera os mesmos dados")] = 42,
    end_date: Annotated[str, typer.Option(help="Último dia dos dados (AAAA-MM-DD)")] = "2026-10-08",
    inject: Annotated[
        list[str], typer.Option(help=f"Cenários de incidente: {', '.join(INCIDENT_SCENARIOS)}")
    ] = [],  # noqa: B006
) -> None:
    """Gera dados sintéticos em data/generated/ (e o manifesto de defeitos, selado)."""
    from novamarket.datagen import generate

    if scale not in SCALES:
        raise typer.BadParameter(f"escala inválida: {scale}")
    result = generate(scale=scale, seed=seed, end_date=date.fromisoformat(end_date),
                      inject=tuple(inject))
    typer.echo(f"Escala {scale} | {result['start_date']} -> {result['end_date']} | seed {seed}")
    for name, n in result["row_counts"].items():
        typer.echo(f"  {name:<40} {n:>10,}")
    typer.echo("Dados em data/generated/. Próximo passo: novamarket data load-erp")


@data_app.command("load-erp")
def data_load_erp() -> None:
    """Carrega o ERP no PostgreSQL local (reinicia as tabelas do ERP)."""
    from novamarket.datagen.erp_loader import load_erp

    for table, n in load_erp().items():
        typer.echo(f"  {table:<22} {n:>10,}")
