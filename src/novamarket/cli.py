from datetime import UTC, date
from typing import Annotated

import typer

from novamarket.datagen.config import INCIDENT_SCENARIOS, SCALES

app = typer.Typer(help="NovaMarket Data Engineering Lab CLI", no_args_is_help=True)
data_app = typer.Typer(help="Geração e carga de dados sintéticos", no_args_is_help=True)
app.add_typer(data_app, name="data")
quality_app = typer.Typer(help="Data Quality", no_args_is_help=True)
app.add_typer(quality_app, name="quality")
pipeline_app = typer.Typer(help="Estado dos pipelines", no_args_is_help=True)
app.add_typer(pipeline_app, name="pipeline")


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


# ------------------------------------------------------------------------------ quality
@quality_app.command("checks")
def quality_checks() -> None:
    """Lista os tipos de check disponíveis."""
    from novamarket.quality import REGISTRY

    for name, fn in sorted(REGISTRY.items()):
        typer.echo(f"  {name:<24} {(fn.__doc__ or '').strip().splitlines()[0] if fn.__doc__ else ''}")


@quality_app.command("list")
def quality_list(config: Annotated[str, typer.Option(help="YAML de checks")] = "") -> None:
    """Lista datasets e quantos checks cada um tem."""
    from pathlib import Path

    from novamarket.quality.runner import load_config

    cfg = load_config(Path(config) if config else None)
    for name, ds in cfg["datasets"].items():
        typer.echo(f"  {name:<28} {len(ds.get('checks', [])):>3} checks   fonte: {ds['source']['type']}")


@quality_app.command("run")
def quality_run(
    datasets: Annotated[list[str], typer.Argument(help="Datasets (vazio = todos)")] = None,
    config: Annotated[str, typer.Option(help="YAML de checks")] = "",
    as_of: Annotated[str, typer.Option(help="Referência de 'agora' para freshness (ISO-8601)")] = "",
    report: Annotated[bool, typer.Option(help="Salvar relatório JSON em data/quality_reports/")] = True,
    only_failures: Annotated[bool, typer.Option(help="Mostrar só o que não passou")] = False,
) -> None:
    """Executa os checks. Sai com código 1 se algum check de severidade `error` falhar."""
    from datetime import datetime
    from pathlib import Path

    from rich.console import Console
    from rich.table import Table

    from novamarket.quality.runner import (
        ConfigError,
        has_blocking_failure,
        load_config,
        run_datasets,
        write_report,
    )

    try:
        cfg = load_config(Path(config) if config else None)
        ref = datetime.fromisoformat(as_of.replace("Z", "+00:00")) if as_of else None
        if ref is not None and ref.tzinfo is None:
            ref = ref.replace(tzinfo=UTC)
        results = run_datasets(cfg, datasets or None, ref)
    except ConfigError as exc:
        typer.echo(f"Configuração inválida: {exc}")
        raise typer.Exit(2) from exc

    table = Table(box=None, pad_edge=False)
    for col in ("dataset", "check", "coluna", "sev", "status", "falhas/total"):
        table.add_column(col)
    for r in results:
        if only_failures and r.status == "pass":
            continue
        style = {"pass": "green", "fail": "red" if r.severity == "error" else "yellow", "error": "magenta"}[r.status]
        table.add_row(r.dataset, r.check, r.column or "-", r.severity, f"[{style}]{r.status}[/{style}]",
                      f"{r.failed}/{r.total}")
    console = Console()
    console.width = max(console.width, 130)  # evita cortar nomes quando a saída não é um terminal
    console.print(table)
    for r in results:
        if r.status != "pass" and (r.samples or r.message):
            typer.echo(f"  {r.dataset}.{r.check}({r.column or ''}): {r.message} {r.samples[:3] if r.samples else ''}")

    passed = sum(r.status == "pass" for r in results)
    typer.echo(f"\n{passed}/{len(results)} checks passaram.")
    if report:
        typer.echo(f"Relatório: {write_report(results)}")
    if has_blocking_failure(results):
        raise typer.Exit(1)


# ---------------------------------------------------------------------------- pipeline
@pipeline_app.command("status")
def pipeline_status(
    as_of: Annotated[str, typer.Option(help="Referência de 'agora' (ISO-8601)")] = "",
    sla: Annotated[str, typer.Option(help="YAML de SLA")] = "",
) -> None:
    """Estado de cada pipeline (OK, FAILED, LATE, SLOW, NEVER_RAN) segundo configs/sla.yaml."""
    from datetime import UTC, datetime
    from pathlib import Path

    from rich.console import Console
    from rich.table import Table

    from novamarket.observability.metrics import RunStore
    from novamarket.observability.status import evaluate, load_sla

    now = datetime.fromisoformat(as_of.replace("Z", "+00:00")) if as_of else datetime.now(UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    rows = evaluate(RunStore().read(), load_sla(Path(sla) if sla else None), now)

    table = Table(box=None, pad_edge=False)
    for col in ("pipeline", "estado", "última execução", "duração(s)", "saída", "rejeitados", "falhas/execuções"):
        table.add_column(col)
    colors = {"OK": "green", "FAILED": "red", "LATE": "yellow", "SLOW": "yellow", "NEVER_RAN": "dim"}
    for r in rows:
        c = colors[r["state"]]
        table.add_row(r["pipeline"], f"[{c}]{r['state']}[/{c}]", r.get("last_finished", "-"),
                      str(r.get("duration_s", "-")), str(r.get("records_out", "-")),
                      str(r.get("records_rejected", "-")), f"{r.get('failures', 0)}/{r.get('runs', 0)}")
    console = Console()
    console.width = max(console.width, 130)
    console.print(table)
    for r in rows:
        if r["detail"]:
            typer.echo(f"  {r['pipeline']}: {r['detail']}")
    if any(r["state"] in ("FAILED", "LATE") for r in rows):
        raise typer.Exit(1)


# ------------------------------------------------------------------- tickets / incidents
ticket_app = typer.Typer(help="Tickets do backlog", no_args_is_help=True)
app.add_typer(ticket_app, name="ticket")
incident_app = typer.Typer(help="Incidentes", no_args_is_help=True)
app.add_typer(incident_app, name="incident")
environment_app = typer.Typer(help="Ambiente local", no_args_is_help=True)
app.add_typer(environment_app, name="environment")


@ticket_app.command("list")
def ticket_list(
    status: Annotated[str, typer.Option(help="Filtrar por estado")] = "",
    all_: Annotated[bool, typer.Option("--all", help="Incluir BACKLOG e DONE")] = False,
) -> None:
    """Lista tickets (por padrão, só os que estão em andamento ou prontos)."""
    from novamarket.work import load_tickets, visible_tickets

    tickets = visible_tickets(load_tickets())
    if status:
        tickets = [t for t in tickets if t["status"] == status.upper()]
    elif not all_:
        tickets = [t for t in tickets if t["status"] in ("READY", "IN_PROGRESS", "BLOCKED", "REVIEW")]
    if not tickets:
        typer.echo("Nenhum ticket para mostrar.")
        return
    for t in tickets:
        typer.echo(f"  {t['id']:<10} {t['status']:<12} nível {t.get('level', '-')}  {t.get('title', '')}")


@ticket_app.command("show")
def ticket_show(ticket_id: str) -> None:
    """Mostra um ticket completo."""
    from novamarket.work import find, load_tickets, visible_tickets

    t = find(visible_tickets(load_tickets()), ticket_id)
    if t is None or t["status"] == "BACKLOG":
        typer.echo(f"Ticket {ticket_id} não encontrado ou ainda não liberado.")
        raise typer.Exit(1)
    for key, value in t.items():
        if key == "hints":  # dicas são liberadas pelo Tech Lead, uma a uma
            continue
        if isinstance(value, list):
            typer.echo(f"{key}:")
            for v in value:
                typer.echo(f"  - {v}")
        else:
            typer.echo(f"{key}: {value}")


@incident_app.command("show")
def incident_show(incident_id: str) -> None:
    """Mostra o incidente (sintomas e impacto; a causa raiz fica selada)."""
    from novamarket.work import find, load_incidents

    inc = find(load_incidents(), incident_id)
    if inc is None or inc.get("status") == "SCHEDULED":
        typer.echo(f"Incidente {incident_id} não encontrado.")
        raise typer.Exit(1)
    for key, value in inc.items():
        typer.echo(f"{key}: {value}")


@incident_app.command("list")
def incident_list() -> None:
    """Lista incidentes já abertos (os agendados só aparecem quando o Tech Lead os libera)."""
    from novamarket.work import load_incidents

    open_ = [i for i in load_incidents() if i.get("status") != "SCHEDULED"]
    if not open_:
        typer.echo("Nenhum incidente aberto.")
    for i in open_:
        typer.echo(f"  {i['id']:<9} {i.get('severity', '-'):<5} {i.get('status', '-'):<12} {i.get('title', '')}")


@environment_app.command("check")
def environment_check() -> None:
    """Verifica ferramentas e serviços locais. Sai com código 1 se algo essencial faltar."""
    from novamarket.environment import run_checks

    results = run_checks()
    for c in results:
        mark = "OK  " if c.ok else "FALTA"
        typer.echo(f"  [{mark}] {c.name:<20} {c.detail}" + (f"  -> {c.hint}" if c.hint else ""))
    optional = {"aws", "terraform", "Airflow UI"}  # não essenciais para começar
    if any(not c.ok and c.name not in optional for c in results):
        raise typer.Exit(1)
