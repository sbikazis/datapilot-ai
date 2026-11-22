# DataPilot AI

**Adaptive Data Intelligence Studio** for CSV, TSV, Excel and JSON datasets. DataPilot profiles each upload first, then lets users investigate it through a workspace shaped around the detected fields.

## Current capabilities

- A dedicated workspace with Overview, Guided Analysis, Decisions, Analysis Studio, Data Explorer, Reports and Settings.
- Configurable workspace name, subtitle, uploaded logo or initials, accent palette, dark appearance by default, with an optional light-mode switch, and compact/comfortable density (session-local).
- Functional analysis defaults for starting view, Top N, numeric precision and report methodology notes.
- CSV, TSV, XLSX, XLS and JSON table ingestion, including worksheet selection for Excel workbooks.
- Automatic field profiling for measures, categories, identifiers and dates, with a reviewable field-role override.
- Conservative semantic hints for percentages, currency-like amounts (without guessing the currency), durations, coordinates, booleans, URLs and personal-data identifiers such as email/phone.
- Global category filters applied across overview findings, analysis views, exploration and reports.
- Adaptive analysis recommendations, descriptive statistics, IQR outlier review, category concentration, date coverage, evidence-backed relationships and sample-aware segment differences with minimum-group-size safeguards.
- Interactive group comparisons, time trends, distributions, scatter plots, category composition and source-row exploration.
- Select marks in comparison, composition and scatter charts to drill into the exact matching source records, preview up to 500 rows and export the selection.
- Client-ready HTML executive report with recipient, author and clearly attributed analyst note; multi-sheet XLSX workbook, CSV extracts and JSON analysis profile.
- A reusable statistical layer with deterministic tests for recommendations, summaries, correlations, category shares and insight evidence.

## First-run experience

Choose **Explore the sample dataset** on the welcome screen to open a reproducible, locally generated fictional orders dataset. It flows through the same profiling, guided analysis, decisions and reporting features as an uploaded file. The sample is clearly labeled synthetic and is not evidence about any real business or customer.

Suggested first steps: compare revenue by region, inspect time movement, review order status and data quality, then export an executive report. Uploading your own file replaces the sample for that session.

## Validation

The automated suite covers individual analysis engines and a full sample-customer journey plus real CSV, XLSX and JSON upload-to-report journeys: file intake, schema and domain detection, guided investigation, evidence ranking, action-register traceability, source-row scope, report metrics, HTML output and workbook tables. Small-sample behavior and the synthetic-data disclosure are also regression-tested.

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


## Transparent file intake

DataPilot reports the detected file format, text encoding and delimiter (or selected Excel worksheet), row/column counts, exact duplicate rows, empty columns, and structural warnings. A read-only source preview is available before deeper analysis. Nested JSON normalization is disclosed. Delimited files with inconsistent row widths are rejected with an actionable error rather than silently dropping malformed records. Intake diagnostics do not automatically repair or rewrite uploaded values; uploads remain session-local.


## Evidence-grounded AI assistance

DataPilot can use the Groq Responses API (model `openai/gpt-oss-20b`) to explain computed results across Overview, Guided Analysis, Decisions and Reports, as well as answer free-form questions in AI Copilot. The deterministic analysis engine remains the source of truth: AI explains existing evidence and does not recalculate or alter metrics.

- Configure `GROQ_API_KEY` in Streamlit Cloud **App settings → Secrets**; never commit the key or paste it into source code.
- Workspace explainers require an explicit **Enable AI explanations** choice in the sidebar and a separate click on the relevant explanation action. No model request runs automatically on page load.
- AI Copilot questions require the user to confirm the data-sharing disclosure and submit the question.
- Requests use aggregate numeric summaries, row counts, field-role metadata and non-sensitive evidence types. Source rows, raw category values and fields with names suggesting direct personal identifiers are excluded.
- Requests use `store: false`. This request-level setting is not a promise about every provider-side operational log or retention obligation; review Groq's current data terms before using confidential or regulated data.
- API calls may incur usage charges under the key's current plan. A connection check calls the models endpoint and does not generate a response; each explanation or question consumes model usage.
- If the key is missing or Groq is unavailable, local profiling, charts, findings and reports continue to work. AI assistance is an enhancement, not a dependency for core analysis.
