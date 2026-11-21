# DataPilot AI

**Adaptive Data Intelligence Studio** for CSV, TSV, Excel and JSON datasets. DataPilot profiles each upload first, then lets users investigate it through a workspace shaped around the detected fields.

## Current capabilities

- A dedicated workspace with Overview, Guided Analysis, Decisions, Analysis Studio, Data Explorer, Reports and Settings.
- Configurable workspace name, subtitle, uploaded logo or initials, accent palette, light/dark appearance and compact/comfortable density (session-local).
- Functional analysis defaults for starting view, Top N, numeric precision and report methodology notes.
- CSV, TSV, XLSX, XLS and JSON table ingestion, including worksheet selection for Excel workbooks.
- Automatic field profiling for measures, categories, identifiers and dates, with a reviewable field-role override.
- Conservative semantic hints for percentages, currency-like amounts (without guessing the currency), durations, coordinates, booleans, URLs and personal-data identifiers such as email/phone.
- Global category filters applied across overview findings, analysis views, exploration and reports.
- Adaptive analysis recommendations, descriptive statistics, IQR outlier review, category concentration, date coverage, evidence-backed relationships and sample-aware segment differences with minimum-group-size safeguards.
- Interactive group comparisons, time trends, distributions, scatter plots, category composition and source-row exploration.
- Select marks in comparison, composition and scatter charts to drill into the exact matching source records, preview up to 500 rows and export the selection.
- HTML executive report, multi-sheet XLSX workbook, CSV extracts and JSON analysis profile.
- A reusable statistical layer with deterministic tests for recommendations, summaries, correlations, category shares and insight evidence.

## First-run experience

Choose **Explore the sample dataset** on the welcome screen to open a reproducible, locally generated fictional orders dataset. It flows through the same profiling, guided analysis, decisions and reporting features as an uploaded file. The sample is clearly labeled synthetic and is not evidence about any real business or customer.

Suggested first steps: compare revenue by region, inspect time movement, review order status and data quality, then export an executive report. Uploading your own file replaces the sample for that session.

## Validation

The automated suite covers individual analysis engines and a full sample-customer journey: schema and domain detection, guided group/time analysis, evidence ranking, action-register traceability, HTML report generation and all nine Excel workbook sheets. Small-sample behavior and the synthetic-data disclosure are also regression-tested.

```bash
pytest -q
```

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest
pytest -q
streamlit run app.py
```

## Trust and limitations

- Automatic findings are deterministic statistics and rules. **This release is not connected to a generative AI model.**
- Findings include denominators and method caveats where applicable; associations do not establish causation.
- IQR outliers are review prompts, not automatic data errors.
- Field-role overrides are user-controlled; ambiguous values should be reviewed before relying on an analysis.
- The app does not invent currency, tax, refund, shipping, inventory, forecasts or other missing business facts.
- Files and workspace preferences are session-local. User accounts, persistent cloud projects, team collaboration, saved report history, native PDF generation and payment processing are not implemented.
- Avoid uploading unnecessary personal or sensitive information.

## Product direction

The next release priorities are deployment verification, accessibility review, broader file diagnostics and commercial readiness. Optional generative AI must remain opt-in, evidence-grounded and privacy-transparent.
