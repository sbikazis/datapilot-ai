# DataPilot AI

Adaptive data intelligence for CSV, TSV, Excel and JSON datasets. DataPilot profiles each uploaded file first, then builds its analysis around the fields and patterns it actually detects.

## What it does

- Detects date/time fields, numeric measures, categories and identifier-like columns.
- Profiles missing values, duplicate records, constant fields and unusually extreme numeric values.
- Produces data-derived findings with plain-language explanations and suggested follow-up checks.
- Supports interactive group comparisons, distributions, time aggregation, correlation matrices and scatter exploration.
- Exports the analyzed dataset and a structured JSON profile.
- Retains a specialist sales analysis when the uploaded data contains the expected sales fields.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest
pytest -q
streamlit run app.py
```

## Supported input formats

CSV, TSV, XLSX, XLS and JSON tables.

The analyzer uses conservative heuristics to classify columns. Always review the detected field roles before relying on a result, especially when numeric-looking identifiers or ambiguous date formats are present.

## Important limits

- Automated findings describe statistical patterns and associations; they do not prove causes.
- Correlation is not causation. Outlier flags are review prompts, not automatic errors.
- The current release does not connect to a generative AI model, external business systems, or live data sources. Its explanations are generated from transparent rules and statistics.
- It does not invent currency, tax, refund, shipping, inventory or other missing business facts.
- It is an analytics aid, not certified accounting or professional advice.
- Files are processed in the app session. Avoid uploading unnecessary personal or sensitive information.
- User accounts, secure persistent storage, payment processing and production security review are not implemented yet.
