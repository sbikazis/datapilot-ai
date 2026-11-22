# DataPilot AI

**Adaptive Data Intelligence Studio** for CSV, TSV, Excel and JSON datasets. DataPilot profiles a dataset, helps users investigate it through evidence-led analysis, and exports executive-ready reports.

## What the product does today

- Upload CSV, TSV, XLSX, XLS and JSON datasets; inspect intake diagnostics and a read-only source preview.
- Detect numeric measures, categories, identifiers and date fields, with user-controlled role overrides.
- Review missing values, duplicates, outliers, date coverage, category concentration and evidence-backed relationships.
- Explore interactive comparisons, time trends, distributions, scatter plots and source-row drill-downs.
- Use Overview, Guided Analysis, Decisions, Analysis Studio, Data Explorer and Reports workspaces.
- Export a self-contained HTML executive report and multi-sheet XLSX workbook, plus CSV extracts and a JSON analysis profile.
- Optionally request evidence-grounded AI explanations across the workspace or ask follow-up questions in AI Copilot using Groq (model `openai/gpt-oss-20b`).
- Choose Light or Dark appearance (Dark is the default), visual themes and interface density.

## First-run demo

Choose **Explore the sample dataset** on the welcome screen to open a reproducible, locally generated fictional orders dataset. It exercises the same profiling, analysis and reporting workflow as an uploaded file. It is clearly labeled synthetic and is not evidence about a real business or customer.

## Trust, privacy and limitations

- Deterministic calculations and rules are the source of truth. AI explains computed evidence; it does not recalculate or alter metrics, and it must not invent currency, causality, forecasts or missing business facts.
- AI is opt-in. Workspace explanations require consent and an explicit action; Copilot requires a separate data-sharing confirmation before a request.
- AI requests use aggregate numeric summaries and metadata rather than source rows or raw category values. Fields that appear to contain direct identifiers or sensitive information are excluded by the context builder. Do not upload confidential, regulated or unnecessary personal data.
- Requests use `store: false`; this request-level setting is not a promise about all provider-side operational logging or retention. Review Groq's current terms before using sensitive business data.
- Uploaded files and workspace preferences are session-local. Persistent accounts, cloud-saved projects, collaboration, saved report history, native PDF generation and in-app payment processing are not implemented.
- DataPilot is an analytical aid, not an accounting system, audit, tax opinion or guarantee of business outcomes. Validate field definitions, source coverage and findings before acting.

## Commercial pilot

DataPilot is being offered initially as a **human-reviewed, one-off sales-data analysis service**, not as a self-serve paid SaaS subscription.

**Pilot deliverable:** a concise executive report based on one customer-provided CSV or Excel export, including data-quality notes, key measures, evidence-led findings, recommended validation steps and an XLSX workbook.

**Introductory test price:** US$49 per report. This is an experimental price, not a published in-app checkout price. Scope and turnaround must be agreed before accepting a customer's file. No payment processing or automated customer-data storage is provided by the app.

See [SALES_OFFER.md](SALES_OFFER.md) for the customer-facing offer and operating boundaries.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest
pytest -q
streamlit run app.py
```

## AI configuration

Set `GROQ_API_KEY` in Streamlit Cloud **App settings → Secrets**. Never commit the key or paste it into source code. If the key is unavailable, local profiling, analysis and exports continue to work without AI.

## Validation

Run the automated test suite with:

```bash
pytest -q
```

The suite covers analysis engines, upload-to-report journeys, report metrics and exports, AI context safeguards, visual themes and UI logic.
