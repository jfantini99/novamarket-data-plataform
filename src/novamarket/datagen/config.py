from dataclasses import dataclass


@dataclass(frozen=True)
class Scale:
    name: str
    customers: int
    products: int
    stores: int  # lojas físicas
    suppliers: int
    dcs: int  # centros de distribuição
    orders: int
    days: int
    stock_per_store: int
    impressions_per_order: float
    ticket_rate: float  # fração de pedidos que geram ticket de atendimento


SCALES: dict[str, Scale] = {
    "tiny": Scale("tiny", 500, 200, 10, 15, 3, 2_000, 14, 80, 3, 0.03),
    "small": Scale("small", 20_000, 2_000, 40, 80, 5, 100_000, 60, 400, 3, 0.03),
    "medium": Scale("medium", 100_000, 10_000, 120, 300, 8, 600_000, 90, 1_500, 2, 0.03),
}

# Cenários de incidente: desligados por padrão, ativados com `--inject`.
INCIDENT_SCENARIOS = ("schema_drift", "truncated_file", "corrupt_records")
