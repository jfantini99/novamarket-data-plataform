"""Gerador de dados sintéticos da NovaMarket.

Determinístico (mesma seed -> mesmos dados). Os defeitos são injetados de propósito e
contabilizados em um manifesto SELADO (.novamarket/_sealed/), que não deve ser lido
antes de investigar.
"""

from __future__ import annotations

import csv
import json
import random
import shutil
import unicodedata
from collections import Counter, defaultdict
from datetime import UTC, date, datetime, time, timedelta, timezone
from pathlib import Path

from novamarket.datagen import catalog as cat
from novamarket.datagen.config import INCIDENT_SCENARIOS, SCALES, Scale

REPO_ROOT = Path(__file__).resolve().parents[3]
UTC = UTC
SOURCES = ("ecommerce", "erp", "logistics", "marketing", "customer_service")


# ---------------------------------------------------------------- helpers de escrita
class JsonlWriter:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.f = open(path, "w", encoding="utf-8", newline="\n")
        self.n = 0

    def write(self, rec: dict) -> None:
        self.f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self.n += 1

    def write_raw(self, line: str) -> None:
        self.f.write(line + "\n")
        self.n += 1

    def close(self) -> None:
        self.f.close()


class CsvWriter:
    def __init__(self, path: Path, header: list[str]):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.f = open(path, "w", encoding="utf-8", newline="")
        self.w = csv.writer(self.f)
        self.w.writerow(header)
        self.n = 0

    def write(self, row: list) -> None:
        self.w.writerow(["" if v is None else v for v in row])
        self.n += 1

    def close(self) -> None:
        self.f.close()


class DailyCsv:
    """Um CSV por dia (drop de arquivos da logística)."""

    def __init__(self, folder: Path, prefix: str, header: list[str]):
        self.folder, self.prefix, self.header = folder, prefix, header
        self.writers: dict[str, CsvWriter] = {}

    def write(self, day: date, row: list) -> None:
        key = day.strftime("%Y%m%d")
        if key not in self.writers:
            self.writers[key] = CsvWriter(self.folder / f"{self.prefix}_{key}.csv", self.header)
        self.writers[key].write(row)

    @property
    def n(self) -> int:
        return sum(w.n for w in self.writers.values())

    def paths(self) -> list[Path]:
        return sorted(Path(w.f.name) for w in self.writers.values())

    def close(self) -> None:
        for w in self.writers.values():
            w.close()


def iso_z(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def fmt_mixed(rng: random.Random, dt: datetime, country: str, d: Counter, tag: str) -> str:
    """Timestamp no formato da fonte e-commerce: mistura UTC, offset local e naive."""
    r = rng.random()
    if r < 0.80:
        return iso_z(dt)
    if r < 0.95:
        d[f"{tag}_local_offset_timestamp"] += 1
        tz = timezone(timedelta(hours=cat.TZ_OFFSET[country]))
        return dt.astimezone(tz).isoformat(timespec="seconds")
    d[f"{tag}_naive_timestamp"] += 1
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def local_naive(dt: datetime, country: str) -> str:
    tz = timezone(timedelta(hours=cat.TZ_OFFSET[country]))
    return dt.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")


def ascii_fold(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def at_midnight(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=UTC)


# ---------------------------------------------------------------------------- ERP
def _gen_erp(rng, sc: Scale, out: Path, d: Counter, start: date, counts: dict):
    erp = out / "erp"
    sup_w = CsvWriter(
        erp / "suppliers.csv",
        ["supplier_id", "supplier_name", "tax_id", "country", "active", "created_at"],
    )
    for sid in range(1, sc.suppliers + 1):
        country = rng.choices(cat.COUNTRIES, cat.COUNTRY_W)[0]
        tax_id = f"{rng.randint(10**13, 10**14 - 1)}"
        if rng.random() < 0.03:
            tax_id = None
            d["supplier_null_tax_id"] += 1
        name = f"{rng.choice(cat.BRANDS)} {rng.choice(cat.LAST_NAMES)} {rng.choice(['Ltda', 'SA', 'Comercial'])}"
        created = datetime(2015, 1, 1) + timedelta(days=rng.randint(0, 3000))
        sup_w.write([sid, name, tax_id, country, rng.random() > 0.05, created.isoformat(sep=" ")])
    sup_w.close()
    counts["erp/suppliers.csv"] = sup_w.n

    store_w = CsvWriter(
        erp / "stores.csv",
        ["store_id", "store_code", "store_name", "store_type", "country", "city", "opened_at", "active"],
    )
    stores = []  # (store_id, type, country)
    store_w.write([1, "ECOM", "NovaMarket Digital", "VIRTUAL", "BR", None, "2012-03-01", True])
    stores.append((1, "VIRTUAL", "BR"))
    sid = 2
    for i in range(sc.dcs):
        country = cat.COUNTRIES[i % len(cat.COUNTRIES)] if i < 5 else "BR"
        city = rng.choice(cat.CITIES[country])[0]
        store_w.write([sid, f"CD-{country}-{i + 1:03d}", f"CD {city}", "DC", country, city,
                       "2014-06-01", True])
        stores.append((sid, "DC", country))
        sid += 1
    for i in range(sc.stores):
        country = rng.choices(cat.COUNTRIES, cat.COUNTRY_W)[0]
        city = rng.choice(cat.CITIES[country])[0]
        opened = date(2005, 1, 1) + timedelta(days=rng.randint(0, 7000))
        store_w.write([sid, f"LJ-{country}-{i + 1:04d}", f"Loja {city} {i + 1}", "STORE", country,
                       city, opened.isoformat(), rng.random() > 0.03])
        stores.append((sid, "STORE", country))
        sid += 1
    store_w.close()
    counts["erp/stores.csv"] = store_w.n

    prod_w = CsvWriter(
        erp / "products.csv",
        ["product_id", "sku", "product_name", "category", "subcategory", "brand", "supplier_id",
         "cost_price", "list_price", "status", "dt_cadastro"],
    )
    products = []  # (product_id, sku, list_price)
    for pid in range(1, sc.products + 1):
        category = rng.choice(list(cat.CATEGORIES))
        sub = rng.choice(cat.CATEGORIES[category])
        brand = rng.choice(cat.BRANDS)
        if rng.random() < 0.04:
            brand = brand.upper() if rng.random() < 0.5 else brand.lower()
            d["product_brand_casing_inconsistent"] += 1
        list_price = round(min(max(rng.lognormvariate(4.3, 0.9), 5), 8000), 2)
        cost = round(list_price * rng.uniform(0.2, 0.6), 2)
        if rng.random() < 0.01:
            cost = round(list_price * rng.uniform(1.05, 1.5), 2)
            d["product_cost_above_price"] += 1
        if rng.random() < 0.03:
            category = sub = None
            d["product_null_category"] += 1
        status = "ACTIVE" if rng.random() < 0.92 else "DISCONTINUED"
        sku = f"NM-{pid:06d}"
        cadastro = date(2018, 1, 1) + timedelta(days=rng.randint(0, 2800))
        prod_w.write([pid, sku, f"{sub or 'Item'} {rng.choice(cat.PRODUCT_WORDS)} {pid}", category,
                      sub, brand, rng.randint(1, sc.suppliers), cost, list_price, status,
                      cadastro.isoformat()])
        products.append((pid, sku, list_price))
    prod_w.close()
    counts["erp/products.csv"] = prod_w.n

    stock_w = CsvWriter(
        erp / "stock.csv",
        ["store_id", "product_id", "quantity_on_hand", "quantity_reserved", "updated_at"],
    )
    for store_id, stype, _ in stores:
        if stype == "VIRTUAL":
            continue
        k = min(sc.stock_per_store * (3 if stype == "DC" else 1), sc.products)
        for p_idx in rng.sample(range(sc.products), k):
            qty = rng.randint(0, 600 if stype == "DC" else 80)
            if rng.random() < 0.002:
                qty = -rng.randint(1, 20)
                d["stock_negative_quantity"] += 1
            updated = None
            if rng.random() >= 0.005:
                updated = (at_midnight(start) + timedelta(seconds=rng.randint(0, 86400 * 30)))
                updated = updated.strftime("%Y-%m-%d %H:%M:%S")
            else:
                d["stock_null_updated_at"] += 1
            stock_w.write([store_id, products[p_idx][0], qty, rng.randint(0, 5), updated])
    stock_w.close()
    counts["erp/stock.csv"] = stock_w.n
    return stores, products


# ------------------------------------------------------------------- clientes e campanhas
def _gen_customers(rng, sc: Scale, out: Path, d: Counter, end: date, counts: dict):
    w = JsonlWriter(out / "ecommerce" / "customers.jsonl")
    customers = []  # (customer_id, country)
    now = at_midnight(end) + timedelta(hours=23)

    def record(cid, country, first, last, email, created, updated, birth):
        city, state = rng.choice(cat.CITIES[country])
        return {
            "customer_id": cid, "first_name": first, "last_name": last, "email": email,
            "phone": f"+{rng.randint(10**10, 10**11 - 1)}", "birth_date": birth,
            "country": country, "state": state, "city": city,
            "loyalty_tier": rng.choices(["NONE", "SILVER", "GOLD", "PLATINUM"], [55, 25, 15, 5])[0],
            "marketing_opt_in": rng.random() < 0.6,
            "created_at": fmt_mixed(rng, created, country, d, "customer"),
            "updated_at": fmt_mixed(rng, updated, country, d, "customer"),
            "_ts": iso_z(updated),
        }

    for cid in range(1, sc.customers + 1):
        country = rng.choices(cat.COUNTRIES, cat.COUNTRY_W)[0]
        first, last = rng.choice(cat.FIRST_NAMES), rng.choice(cat.LAST_NAMES)
        email = f"{ascii_fold(first)}.{ascii_fold(last)}{rng.randint(1, 9999)}@{rng.choice(cat.EMAIL_DOMAINS)}"
        r = rng.random()
        if r < 0.03:
            email = None
            d["customer_null_email"] += 1
        elif r < 0.04:
            email = email.replace("@", "")
            d["customer_invalid_email"] += 1
        birth = (date(1950, 1, 1) + timedelta(days=rng.randint(0, 19000))).isoformat()
        if rng.random() < 0.01:
            birth = rng.choice(["0000-00-00", "2031-05-10", "1900-01-01"])
            d["customer_invalid_birth_date"] += 1
        created = now - timedelta(days=rng.randint(60, 1500), seconds=rng.randint(0, 86399))
        updated = created
        if rng.random() < 0.3:
            updated = min(now, created + timedelta(days=rng.randint(1, 1400)))
        rec = record(cid, country, first, last, email, created, updated, birth)
        w.write(rec)
        if rng.random() < 0.005:
            w.write(rec)
            d["customer_exact_duplicate_row"] += 1
        customers.append((cid, country))

    # mesma pessoa cadastrada duas vezes com IDs diferentes
    next_id = sc.customers + 1
    for _cid, country in rng.sample(customers, int(sc.customers * 0.02)):
        first, last = rng.choice(cat.FIRST_NAMES), rng.choice(cat.LAST_NAMES)
        email = f"{ascii_fold(first)}.{ascii_fold(last)}{rng.randint(1, 9999)}@{rng.choice(cat.EMAIL_DOMAINS)}"
        created = now - timedelta(days=rng.randint(1, 60))
        w.write(record(next_id, country, first, last, email.upper(), created, created, "1990-01-01"))
        d["customer_duplicate_person_new_id"] += 1
        next_id += 1
    w.close()
    counts["ecommerce/customers.jsonl"] = w.n
    return customers


def _gen_campaigns(rng, sc: Scale, out: Path, d: Counter, start: date, end: date, counts: dict):
    w = JsonlWriter(out / "marketing" / "campaigns.jsonl")
    campaigns = []  # (id, channel, start, end)
    n = max(8, sc.days // 2)
    for cid in range(1, n + 1):
        cs = start - timedelta(days=15) + timedelta(days=rng.randint(0, sc.days + 10))
        ce = cs + timedelta(days=rng.randint(7, 45))
        channel = rng.choice(cat.CAMPAIGN_CHANNELS)
        campaigns.append((cid, channel, cs, ce))
        out_end, budget = ce.isoformat(), round(rng.uniform(5_000, 400_000), 2)
        if rng.random() < 0.03:
            out_end = (cs - timedelta(days=rng.randint(1, 10))).isoformat()
            d["campaign_end_before_start"] += 1
        if rng.random() < 0.05:
            budget = None
            d["campaign_null_budget"] += 1
        w.write({
            "campaign_id": cid, "name": f"{channel.title()} {cs:%b/%y} #{cid}", "channel": channel,
            "budget": budget, "start_date": cs.isoformat(), "end_date": out_end,
            "status": "ENDED" if ce < end else "ACTIVE", "_ts": iso_z(at_midnight(cs)),
        })
    w.close()
    counts["marketing/campaigns.jsonl"] = w.n
    by_day: dict[date, list] = {}
    for i in range(-15, sc.days + 1):
        day = start + timedelta(days=i)
        by_day[day] = [c for c in campaigns if c[2] <= day <= c[3]]
    return by_day


# --------------------------------------------------------------------------- marketing
class Marketing:
    def __init__(self, rng, out: Path, d: Counter, inject, counts: dict):
        m = out / "marketing"
        self.rng, self.d, self.inject, self.counts = rng, d, inject, counts
        self.imp = JsonlWriter(m / "impressions.jsonl")
        self.clk = JsonlWriter(m / "clicks.jsonl")
        self.cnv = JsonlWriter(m / "conversions.jsonl")
        self.n_imp = self.n_clk = self.n_cnv = 0

    @staticmethod
    def _ts(dt: datetime) -> str:
        return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"

    def impression(self, campaign_id, user_ref, dt, placement=None) -> int:
        self.n_imp += 1
        self.imp.write({
            "impression_id": self.n_imp, "campaign_id": campaign_id, "user_ref": user_ref,
            "placement": placement or self.rng.choice(cat.PLACEMENTS),
            "occurred_at": self._ts(dt), "_ts": iso_z(dt),
        })
        return self.n_imp

    def click(self, impression_id, campaign_id, customer_id, dt) -> int:
        rng, d = self.rng, self.d
        self.n_clk += 1
        if rng.random() < 0.005:
            impression_id = None
            d["click_without_impression"] += 1
        if rng.random() < 0.002:
            dt -= timedelta(hours=rng.randint(1, 48))
            d["click_before_impression"] += 1
        rec = {
            "click_id": self.n_clk, "impression_id": impression_id, "campaign_id": campaign_id,
            "customer_id": customer_id, "occurred_at": self._ts(dt), "_ts": iso_z(dt),
        }
        if "corrupt_records" in self.inject and rng.random() < 0.005:
            line = json.dumps(rec)
            self.clk.write_raw(line[: len(line) // 2])
            d["corrupt_click_line"] += 1
        else:
            self.clk.write(rec)
        return self.n_clk

    def conversion(self, click_id, order_id, campaign_id, revenue, dt) -> None:
        rng, d = self.rng, self.d
        self.n_cnv += 1
        if rng.random() < 0.003:
            order_id += 10_000_000
            d["conversion_unknown_order"] += 1
        rec = {
            "conversion_id": self.n_cnv, "click_id": click_id, "order_id": order_id,
            "campaign_id": campaign_id, "attributed_revenue": revenue,
            "occurred_at": self._ts(dt), "_ts": iso_z(dt),
        }
        self.cnv.write(rec)
        if rng.random() < 0.01:
            self.cnv.write(rec)
            d["conversion_duplicate_row"] += 1

    def chain(self, order_id, customer_id, created, campaign, revenue) -> None:
        rng = self.rng
        t_imp = created - timedelta(minutes=rng.randint(10, 2000))
        imp = self.impression(campaign, customer_id, t_imp)
        t_clk = t_imp + timedelta(seconds=rng.randint(5, 600))
        clk = self.click(imp, campaign, customer_id, t_clk)
        self.conversion(clk, order_id, campaign, revenue, created)

    def noise(self, sc: Scale, start: date, by_day: dict, customers) -> None:
        rng = self.rng
        n = int(sc.orders * sc.impressions_per_order)
        for _ in range(n):
            day = start + timedelta(days=rng.randrange(sc.days))
            active = by_day.get(day)
            if not active:
                continue
            c = rng.choice(active)
            dt = at_midnight(day) + timedelta(seconds=rng.randint(0, 86399))
            user = rng.choice(customers)[0] if rng.random() < 0.4 else f"anon-{rng.randint(1, 10**7)}"
            imp = self.impression(c[0], user, dt)
            if rng.random() < cat.CTR[c[1]]:
                cust = user if isinstance(user, int) else None
                self.click(imp, c[0], cust, dt + timedelta(seconds=rng.randint(2, 900)))

    def close(self) -> None:
        for name, w in (("impressions", self.imp), ("clicks", self.clk), ("conversions", self.cnv)):
            w.close()
            self.counts[f"marketing/{name}.jsonl"] = w.n


# --------------------------------------------------------------------------- comércio
def _gen_commerce(rng, sc, out, d, start, end, customers, stores, products, by_day, mkt, inject,
                  counts):
    ew = out / "ecommerce"
    ow = JsonlWriter(ew / "orders.jsonl")
    iw = JsonlWriter(ew / "order_items.jsonl")
    pw = JsonlWriter(ew / "payments.jsonl")
    physical = defaultdict(list)
    for sid, stype, country in stores:
        if stype == "STORE":
            physical[country].append(sid)
    all_physical = [s for v in physical.values() for s in v]
    day_w = [
        (1.25 if (start + timedelta(days=i)).weekday() in (4, 5) else 1.0) * (1 + 0.4 * i / sc.days)
        for i in range(sc.days)
    ]
    day_idx = sorted(rng.choices(range(sc.days), day_w, k=sc.orders))
    drift_from = end - timedelta(days=2) if "schema_drift" in inject else None
    cap = at_midnight(end) + timedelta(hours=23, minutes=59, seconds=59)
    orders = []
    item_id = pay_id = 0

    for oid, di in enumerate(day_idx, start=1):
        day = start + timedelta(days=di)
        created = at_midnight(day) + timedelta(seconds=int(rng.triangular(0, 86399, 68000)))
        cust_id, country = customers[int(len(customers) * rng.random() ** 1.8)]
        channel = rng.choices(cat.CHANNELS, cat.CHANNEL_W)[0]
        if channel == "store":
            store_id = rng.choice(physical.get(country) or all_physical)
        else:
            store_id = 1
        fx = cat.FX[country]

        subtotal = 0.0
        items = []
        for _ in range(rng.choices([1, 2, 3, 4, 5, 6], [40, 28, 15, 9, 5, 3])[0]):
            p = products[int(len(products) * rng.random() ** 1.6)]
            qty = rng.choices([1, 2, 3, 4], [70, 20, 7, 3])[0]
            price = round(p[2] * fx * (1 - rng.choice([0, 0, 0, 0.05, 0.1, 0.15])), 2)
            r = rng.random()
            if r < 0.001:
                qty = 9999
                d["item_extreme_quantity"] += 1
            elif r < 0.002:
                qty = 0
                d["item_zero_quantity"] += 1
            elif r < 0.0025:
                price = -price
                d["item_negative_price"] += 1
            elif r < 0.0045:
                price = None
                d["item_null_price"] += 1
            sku = p[1]
            if rng.random() < 0.01:
                sku = sku.lower() if rng.random() < 0.5 else sku + " "
                d["item_sku_format_variant"] += 1
            subtotal += qty * (price or 0)
            items.append((sku, qty, price))

        shipping = 0.0 if channel == "store" else round(rng.choice([0, 0, 9.9, 14.9, 19.9, 29.9]) * fx, 2)
        order_disc = round(subtotal * rng.choice([0, 0, 0, 0, 0.05, 0.1]), 2)
        total = round(subtotal - order_disc + shipping, 2)

        # status e atualização
        age = (end - day).days
        r = rng.random()
        if channel == "store":
            status, delay = "COMPLETED", timedelta(minutes=rng.randint(0, 5))
        elif r < 0.04:
            status, delay = "CANCELED", timedelta(hours=rng.randint(1, 30))
        elif age <= 0:
            status, delay = ("CREATED", timedelta()) if r < 0.3 else ("PAID", timedelta(minutes=rng.randint(1, 30)))
        elif age <= 2:
            status, delay = ("SHIPPED", timedelta(days=1, hours=rng.randint(0, 12))) if r < 0.7 else (
                "PAID", timedelta(minutes=rng.randint(1, 30)))
        elif r > 0.96 and age > 7:
            status, delay = "RETURNED", timedelta(days=rng.randint(8, 15))
        else:
            status, delay = "DELIVERED", timedelta(days=rng.randint(2, 6), hours=rng.randint(0, 20))
        updated = created + delay
        if rng.random() < 0.01:
            updated += timedelta(days=rng.randint(3, 10))
            d["order_late_arriving_update"] += 1
        updated = min(updated, cap)

        emitted_total = total
        if rng.random() < 0.005:
            emitted_total = round(total + rng.choice([-1, 1]) * rng.uniform(5, 200) * fx, 2)
            d["order_total_mismatch_items"] += 1

        campaign = None
        if channel != "store" and rng.random() < 0.25:
            active = by_day.get(day)
            if active:
                campaign = rng.choice(active)[0]
        out_cust = cust_id
        if rng.random() < 0.002:
            out_cust = None
            d["order_null_customer"] += 1

        rec = {
            "order_id": oid, "customer_id": out_cust, "channel": channel, "store_id": store_id,
            "status": status, "currency": cat.CURRENCY[country], "country": country,
            "total_amount": emitted_total, "discount_amount": order_disc,
            "shipping_amount": shipping, "campaign_id": campaign,
            "created_at": fmt_mixed(rng, created, country, d, "order"),
            "updated_at": fmt_mixed(rng, updated, country, d, "order"),
            "_ts": iso_z(updated),
        }
        if drift_from and day >= drift_from:
            rec["order_total"] = rec.pop("total_amount")
            rec["order_created_at"] = rec.pop("created_at")
            d["schema_drift_orders"] += 1
        ow.write(rec)
        if rng.random() < 0.01:
            ow.write(rec)
            d["order_duplicate_row"] += 1

        for sku, qty, price in items:
            item_id += 1
            iw.write({
                "order_item_id": item_id, "order_id": oid, "product_sku": sku, "quantity": qty,
                "unit_price": price, "_ts": iso_z(updated),
            })

        # pagamento
        pay_id += 1
        if status in ("CANCELED",):
            pstatus = "DECLINED" if rng.random() < 0.6 else "REFUNDED"
        elif status == "RETURNED":
            pstatus = "REFUNDED"
        elif status == "CREATED":
            pstatus = "PENDING"
        else:
            pstatus = "APPROVED"
        if rng.random() < 0.02:
            pstatus = pstatus.capitalize() if rng.random() < 0.5 else pstatus.lower()
            d["payment_status_casing_variant"] += 1
        method = rng.choice(cat.PAYMENT_METHODS if country == "BR" else
                            [m for m in cat.PAYMENT_METHODS if m not in ("PIX", "BOLETO")])
        paid_at = None if pstatus.upper() in ("PENDING", "DECLINED") else iso_z(created + timedelta(seconds=rng.randint(5, 900)))
        prec = {
            "payment_id": pay_id, "order_id": oid, "method": method, "status": pstatus,
            "amount": emitted_total, "installments": rng.randint(1, 12) if method == "CREDIT_CARD" else 1,
            "paid_at": paid_at, "updated_at": iso_z(updated), "_ts": iso_z(updated),
        }
        pw.write(prec)
        if rng.random() < 0.01:
            pw.write(prec)
            d["payment_duplicate_row"] += 1

        if campaign:
            mkt.chain(oid, cust_id, created, campaign, emitted_total)

        orders.append((oid, created, updated, country, channel, status, cust_id))

    for name, w in (("orders", ow), ("order_items", iw), ("payments", pw)):
        w.close()
        counts[f"ecommerce/{name}.jsonl"] = w.n
    return orders


# ---------------------------------------------------------------------------- logística
def _gen_logistics(rng, sc, out, d, end, orders, stores, inject, counts):
    folder = out / "logistics"
    dcs = [s[0] for s in stores if s[1] == "DC"]
    ship = DailyCsv(folder, "shipments", [
        "shipment_id", "order_id", "dc_id", "carrier", "tracking_code", "status", "shipped_at",
        "estimated_delivery", "delivered_at", "weight_kg", "freight_cost"])
    evt = DailyCsv(folder, "delivery_events", [
        "event_id", "shipment_id", "event_type", "event_at", "location", "notes"])
    cap = at_midnight(end) + timedelta(hours=23, minutes=59)
    sid = eid = 0

    def event(shipment_id, etype, dt, country, note=None):
        nonlocal eid
        eid += 1
        city = rng.choice(cat.CITIES[country])[0]
        row = [eid, shipment_id, etype, local_naive(dt, country), city, note]
        evt.write(dt.astimezone(timezone(timedelta(hours=cat.TZ_OFFSET[country]))).date(), row)
        if rng.random() < 0.01:
            evt.write(dt.astimezone(timezone(timedelta(hours=cat.TZ_OFFSET[country]))).date(), row)
            d["delivery_event_duplicate_row"] += 1

    for oid, created, _updated, country, channel, status, _ in orders:
        if channel == "store" or status not in ("SHIPPED", "DELIVERED", "RETURNED"):
            continue
        shipped = created + timedelta(hours=rng.randint(4, 36))
        if shipped > cap:
            continue
        sid += 1
        carrier = rng.choices(cat.CARRIERS, [35, 30, 20, 15])[0]
        out_carrier = carrier
        if rng.random() < 0.01:
            out_carrier = None
            d["shipment_null_carrier"] += 1
        est = shipped + timedelta(days=rng.randint(2, 8))
        delivered = None
        if status in ("DELIVERED", "RETURNED"):
            delivered = min(shipped + timedelta(days=rng.randint(1, 7), hours=rng.randint(0, 12)), cap)
            if rng.random() < 0.003:
                delivered = shipped - timedelta(hours=rng.randint(1, 48))
                d["shipment_delivered_before_shipped"] += 1
        freight = round(rng.uniform(8, 80), 2)
        freight_out = str(freight).replace(".", ",") if carrier == "MercoExpress" else freight
        ship.write(shipped.astimezone(timezone(timedelta(hours=cat.TZ_OFFSET[country]))).date(), [
            sid, oid, rng.choice(dcs), out_carrier, f"NM{rng.randint(10**9, 10**10 - 1)}",
            "DELIVERED" if delivered else "IN_TRANSIT", local_naive(shipped, country),
            local_naive(est, country), local_naive(delivered, country) if delivered else None,
            round(rng.uniform(0.2, 25), 2), freight_out])

        event(sid, "PICKED_UP", shipped, country)
        t = shipped
        for _ in range(rng.randint(1, 3)):
            t += timedelta(hours=rng.randint(6, 30))
            if t < cap:
                event(sid, "IN_TRANSIT", t, country)
        if delivered:
            if rng.random() < 0.12:
                event(sid, "FAILED_ATTEMPT", delivered - timedelta(hours=5), country, "ausente")
            event(sid, "OUT_FOR_DELIVERY", delivered - timedelta(hours=3), country)
            event(sid, "DELIVERED", delivered, country)
            if status == "RETURNED":
                event(sid, "RETURNED", min(delivered + timedelta(days=rng.randint(2, 8)), cap), country)
        if rng.random() < 0.002:
            event(sid + 5_000_000, "IN_TRANSIT", t, country, "remessa desconhecida")
            d["delivery_event_unknown_shipment"] += 1

    paths = ship.paths()
    ship.close()
    evt.close()
    counts["logistics/shipments_*.csv"] = ship.n
    counts["logistics/delivery_events_*.csv"] = evt.n
    if "truncated_file" in inject and paths:
        last = paths[-1]
        data = last.read_bytes()
        last.write_bytes(data[: int(len(data) * 0.6)])
        d["truncated_logistics_file"] += 1


# ------------------------------------------------------------------ atendimento ao cliente
def _gen_customer_service(rng, sc, out, d, end, orders, counts):
    cs = out / "customer_service"
    tw = CsvWriter(cs / "tickets.csv", [
        "ticket_id", "customer_id", "order_id", "channel", "category", "priority", "status",
        "created_at", "resolved_at", "subject"])
    iw = JsonlWriter(cs / "interactions.jsonl")
    cw = CsvWriter(cs / "complaints.csv", [
        "complaint_id", "ticket_id", "order_id", "type", "severity", "regulator_flag", "created_at"])
    cap = at_midnight(end) + timedelta(hours=23)
    n_orders = len(orders)
    tid = iid = cid = 0
    for oid, _created, updated, country, channel, _status, cust in orders:
        if rng.random() >= sc.ticket_rate * (0.4 if channel == "store" else 1.2):
            continue
        tid += 1
        order_ref = oid
        if rng.random() < 0.2:
            order_ref = None
        elif rng.random() < 0.005:
            order_ref = n_orders + rng.randint(1, 5000)
            d["ticket_unknown_order"] += 1
        opened = min(updated + timedelta(hours=rng.randint(1, 120)), cap)
        resolved_status = rng.choices(["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"], [8, 7, 45, 40])[0]
        resolved = None
        if resolved_status in ("RESOLVED", "CLOSED"):
            resolved = opened + timedelta(hours=rng.randint(1, 200))
            if rng.random() < 0.01:
                resolved = opened - timedelta(hours=rng.randint(1, 48))
                d["ticket_resolved_before_created"] += 1
        category = rng.choice(cat.TICKET_CATEGORIES)
        if rng.random() < 0.03:
            category = None
            d["ticket_null_category"] += 1
        row = [tid, cust, order_ref, rng.choice(["PHONE", "CHAT", "EMAIL", "APP"]), category,
               rng.choice(["LOW", "MEDIUM", "HIGH"]), resolved_status,
               local_naive(opened, country), local_naive(resolved, country) if resolved else None,
               rng.choice(cat.TICKET_MESSAGES)[:40]]
        tw.write(row)
        if rng.random() < 0.01:
            tw.write(row)
            d["ticket_duplicate_row"] += 1
        t = opened
        for k in range(rng.randint(1, 5)):
            iid += 1
            msg = rng.choice(cat.TICKET_MESSAGES)
            if rng.random() < 0.01:
                msg = msg.encode("utf-8").decode("latin-1")
                d["interaction_encoding_garbled"] += 1
            iw.write({
                "interaction_id": iid, "ticket_id": tid, "agent_id": f"AG{rng.randint(1, 120):03d}",
                "direction": "INBOUND" if k % 2 == 0 else "OUTBOUND", "message": msg,
                "occurred_at": iso_z(t),
            })
            t += timedelta(hours=rng.randint(1, 30))
        if rng.random() < 0.10:
            cid += 1
            cw.write([cid, tid, order_ref, rng.choice(["DELAY", "DEFECT", "BILLING", "FRAUD"]),
                      rng.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]), rng.random() < 0.15,
                      local_naive(opened, country)])
    for name, w in (("tickets.csv", tw), ("interactions.jsonl", iw), ("complaints.csv", cw)):
        w.close()
        counts[f"customer_service/{name}"] = w.n


# ------------------------------------------------------------------------- orquestração
def generate(scale: str = "small", seed: int = 42, out_dir: Path | None = None,
             end_date: date = date(2026, 10, 8), inject: tuple[str, ...] = (),
             manifest_dir: Path | None = None) -> dict:
    if scale not in SCALES:
        raise ValueError(f"escala inválida: {scale}")
    bad = set(inject) - set(INCIDENT_SCENARIOS)
    if bad:
        raise ValueError(f"cenários inválidos: {sorted(bad)}")
    sc = SCALES[scale]
    rng = random.Random(seed)
    out = Path(out_dir) if out_dir else REPO_ROOT / "data" / "generated"
    manifest_dir = Path(manifest_dir) if manifest_dir else REPO_ROOT / ".novamarket" / "_sealed"
    for src in SOURCES:  # só apaga o que este gerador cria
        shutil.rmtree(out / src, ignore_errors=True)

    d: Counter = Counter()
    counts: dict[str, int] = {}
    start = end_date - timedelta(days=sc.days - 1)

    stores, products = _gen_erp(rng, sc, out, d, start, counts)
    customers = _gen_customers(rng, sc, out, d, end_date, counts)
    by_day = _gen_campaigns(rng, sc, out, d, start, end_date, counts)
    mkt = Marketing(rng, out, d, inject, counts)
    orders = _gen_commerce(rng, sc, out, d, start, end_date, customers, stores, products, by_day,
                           mkt, inject, counts)
    mkt.noise(sc, start, by_day, customers)
    mkt.close()
    _gen_logistics(rng, sc, out, d, end_date, orders, stores, inject, counts)
    _gen_customer_service(rng, sc, out, d, end_date, orders, counts)

    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "scale": scale, "seed": seed, "start_date": start.isoformat(), "end_date": end_date.isoformat(),
        "injected_scenarios": list(inject), "generated_at": datetime.now(UTC).isoformat(),
        "defects": dict(sorted(d.items())), "row_counts": counts,
    }
    (manifest_dir / "defects_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"scale": scale, "seed": seed, "start_date": start, "end_date": end_date, "row_counts": counts}
