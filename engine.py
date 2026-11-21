from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import BinaryIO
import re

import pandas as pd

REQUIRED = ["order_id", "order_date", "product", "category", "quantity", "unit_price", "unit_cost"]
OPTIONAL = ["customer_region"]
ALIASES = {
    "order_id": {"order_id", "orderid", "order_number", "invoice", "invoice_id", "id_commande", "numero_commande"},
    "order_date": {"order_date", "date", "purchase_date", "transaction_date", "date_commande"},
    "product": {"product", "product_name", "item", "item_name", "article", "produit"},
    "category": {"category", "product_category", "type", "categorie"},
    "quantity": {"quantity", "qty", "units", "units_sold", "quantite"},
    "unit_price": {"unit_price", "price", "selling_price", "sale_price", "prix_unitaire"},
    "unit_cost": {"unit_cost", "cost", "cost_price", "purchase_cost", "cout_unitaire"},
    "customer_region": {"customer_region", "region", "area", "location", "region_client"},
}


def _normalise_name(value: object) -> str:
    text = str(value).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text


def map_columns(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    """Rename recognised headers. Raises when multiple input columns map to one field."""
    reverse = {alias: canonical for canonical, aliases in ALIASES.items() for alias in aliases | {canonical}}
    mapping: dict[str, str] = {}
    claimed: dict[str, str] = {}
    for original in frame.columns:
        normal = _normalise_name(original)
        canonical = reverse.get(normal)
        if canonical:
            if canonical in claimed:
                raise ValueError(f"Both '{claimed[canonical]}' and '{original}' map to '{canonical}'. Keep only one.")
            mapping[str(original)] = canonical
            claimed[canonical] = str(original)
    return frame.rename(columns=mapping).copy(), mapping


def load_sales_file(file: str | BinaryIO | BytesIO, filename: str | None = None) -> pd.DataFrame:
    """Load CSV or Excel without guessing a currency."""
    name = (filename or getattr(file, "name", "")).lower()
    if name.endswith((".xlsx", ".xls")):
        frame = pd.read_excel(file)
    else:
        try:
            frame = pd.read_csv(file)
        except UnicodeDecodeError:
            if hasattr(file, "seek"):
                file.seek(0)
            frame = pd.read_csv(file, encoding="latin-1")
    frame, _ = map_columns(frame)
    return frame


@dataclass
class AnalysisResult:
    clean: pd.DataFrame
    rejected: pd.DataFrame
    summary: dict
    by_product: pd.DataFrame
    by_category: pd.DataFrame
    by_month: pd.DataFrame
    column_mapping: dict[str, str]


def analyze_sales(frame: pd.DataFrame) -> AnalysisResult:
    data, mapping = map_columns(frame)
    missing = [column for column in REQUIRED if column not in data.columns]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))

    work = data.copy()
    work["_source_row"] = range(2, len(work) + 2)
    reasons: list[list[str]] = [[] for _ in range(len(work))]

    for column in ["order_id", "product", "category"]:
        invalid = work[column].isna() | work[column].astype(str).str.strip().eq("")
        for idx in work.index[invalid]:
            reasons[work.index.get_loc(idx)].append(f"{column} is missing")

    parsed_dates = pd.to_datetime(work["order_date"], errors="coerce", dayfirst=True)
    for pos, bad in enumerate(parsed_dates.isna()):
        if bad:
            reasons[pos].append("order_date is missing or invalid")
    work["order_date"] = parsed_dates

    for column in ["quantity", "unit_price", "unit_cost"]:
        work[column] = pd.to_numeric(work[column], errors="coerce")
        for pos, value in enumerate(work[column].tolist()):
            if pd.isna(value):
                reasons[pos].append(f"{column} is missing or not numeric")
            elif value < 0 or (column == "quantity" and value <= 0):
                reasons[pos].append(f"{column} must be {'greater than zero' if column == 'quantity' else 'zero or greater'}")

    reason_text = ["; ".join(dict.fromkeys(items)) for items in reasons]
    work["rejection_reason"] = reason_text
    rejected = work[work["rejection_reason"].ne("")].copy()
    clean = work[work["rejection_reason"].eq("")].drop(columns=["rejection_reason"]).copy()

    if clean.empty:
        raise ValueError("No valid sales rows remain after validation. Review the rejected rows.")

    clean["revenue"] = clean["quantity"] * clean["unit_price"]
    clean["cost"] = clean["quantity"] * clean["unit_cost"]
    clean["gross_profit"] = clean["revenue"] - clean["cost"]
    clean["gross_margin_pct"] = clean["gross_profit"].div(clean["revenue"].where(clean["revenue"].ne(0))).mul(100)
    clean["month"] = clean["order_date"].dt.to_period("M").astype(str)

    total_revenue = float(clean["revenue"].sum())
    total_cost = float(clean["cost"].sum())
    total_profit = total_revenue - total_cost
    order_count = int(clean["order_id"].nunique())
    summary = {
        "valid_rows": int(len(clean)),
        "rejected_rows": int(len(rejected)),
        "order_count": order_count,
        "total_revenue": total_revenue,
        "total_cost": total_cost,
        "gross_profit": total_profit,
        "gross_margin_pct": (total_profit / total_revenue * 100) if total_revenue else None,
        "average_order_value": (total_revenue / order_count) if order_count else None,
    }

    by_product = clean.groupby("product", dropna=False).agg(units=("quantity", "sum"), revenue=("revenue", "sum"), gross_profit=("gross_profit", "sum")).reset_index().sort_values("revenue", ascending=False)
    by_category = clean.groupby("category", dropna=False).agg(units=("quantity", "sum"), revenue=("revenue", "sum"), gross_profit=("gross_profit", "sum")).reset_index().sort_values("revenue", ascending=False)
    by_month = clean.groupby("month", dropna=False).agg(revenue=("revenue", "sum"), gross_profit=("gross_profit", "sum")).reset_index().sort_values("month")

    return AnalysisResult(clean, rejected, summary, by_product, by_category, by_month, mapping)


def build_html_report(result: AnalysisResult) -> str:
    s = result.summary
    def money(value):
        return "Not available" if value is None else f"{value:,.2f}"
    metrics = [
        ("Revenue", money(s["total_revenue"])), ("Cost", money(s["total_cost"])),
        ("Gross profit", money(s["gross_profit"])),
        ("Gross margin", "Not available" if s["gross_margin_pct"] is None else f'{s["gross_margin_pct"]:.2f}%'),
        ("Orders", str(s["order_count"])), ("Average order value", money(s["average_order_value"])),
    ]
    cards = "".join(f"<article><small>{label}</small><strong>{value}</strong></article>" for label, value in metrics)
    products = result.by_product.to_html(index=False, border=0, classes="data")
    months = result.by_month.to_html(index=False, border=0, classes="data")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DataPilot AI report</title><style>
    body{{font:15px system-ui,sans-serif;max-width:1050px;margin:40px auto;padding:0 20px;color:#202033;background:#faf9ff}}h1{{color:#4b2b83}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}}article{{background:white;border:1px solid #e8e2f2;border-radius:12px;padding:16px}}small{{display:block;color:#686477}}strong{{display:block;font-size:22px;margin-top:8px}}table{{border-collapse:collapse;width:100%;background:white;margin:12px 0 28px}}th,td{{padding:9px;border-bottom:1px solid #eee;text-align:left}}th{{background:#f0ebf8}}.note{{color:#666;font-size:13px}}
    </style></head><body><h1>DataPilot AI — Sales report</h1><p>Based only on the valid rows in the uploaded dataset. No currency has been assumed.</p><section class="grid">{cards}</section><h2>Product performance</h2>{products}<h2>Monthly performance</h2>{months}<p class="note">Gross profit is revenue minus recorded unit cost. This is not certified accounting advice. Taxes, returns, shipping and payment fees are excluded unless present in the source data.</p></body></html>"""
