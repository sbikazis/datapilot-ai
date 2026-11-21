# DataPilot AI

A first working MVP for small businesses to clean sales exports and understand revenue, recorded costs, gross profit, margin, order value, product performance and monthly trends.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest
pytest -q test_engine.py
streamlit run app.py
```

## Input format

Required fields (common aliases are detected): `order_id`, `order_date`, `product`, `category`, `quantity`, `unit_price`, `unit_cost`. Optional: `customer_region`.

## Outputs

- Cleaned CSV with calculated revenue, cost, gross profit and margin.
- Rejected-row CSV with explicit validation reasons.
- Printable HTML report.

## Calculation definitions

- Revenue = quantity × unit price
- Cost = quantity × unit cost
- Gross profit = revenue − cost
- Gross margin = gross profit ÷ revenue × 100
- Average order value = revenue ÷ distinct order count

No currency, tax, returns, shipping, payment fees or inventory values are inferred. Those are included only when supported by source data. This is an analytics aid, not certified accounting software.

## Privacy

Use only data you are authorized to process. Avoid unnecessary personal/customer information. Do not publish customer-level exports or reports publicly.

## Current status

This is an early MVP. Hosting, payment processing, user accounts, secure persistent storage and production security review are not yet implemented.
