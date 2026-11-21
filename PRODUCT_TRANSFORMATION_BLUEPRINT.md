# DataPilot AI — Product Transformation Blueprint

## Product promise
DataPilot AI is an adaptive analytics workspace: it should understand the structure and likely meaning of a dataset, let the user interrogate it visually, explain what the evidence supports, and produce a useful decision-ready report. It must not pretend every file is a sales table or invent causes, forecasts, currency, or business context.

## Product quality bar
A release is not complete because the app imports or displays a few KPIs. Each release must pass:
- Correctness: deterministic tests for profiling, calculations, chart construction, exports, and edge cases.
- Adaptivity: numeric, categorical, date, mixed, wide, sparse, and domain-specific datasets.
- Explainability: every finding shows its metric, baseline, evidence, limitations, and concrete next question.
- Interactivity: chart selections, filters, drill-downs, and comparisons update the analysis rather than act as decoration.
- Presentation: coherent visual system, responsive layouts, clear empty/loading/error states, and accessible contrast.
- Trust: source data remains recoverable; transformations are disclosed; no unsupported business claims.

## Workstreams

### 0 — Reliability and regression protection
- Fix the time-series chart crash caused by passing unsupported area=True to Plotly Express line.
- Centralize chart construction and add rendering regression tests.
- Test empty time windows, invalid dates, all-null measures, one-row data, and unsupported aggregation.
- Add a smoke test for each major tab using representative datasets.

### 1 — Product identity and application shell
- Establish a distinctive DataPilot visual identity: logo mark, typography, color tokens, spacing, iconography, and chart palette.
- Build stable navigation with Overview, Analyze, Data Explorer, Reports, and Settings.
- Add workspace identity controls: editable workspace name, logo/avatar, theme, density, and chart preferences.
- Persist non-sensitive preferences appropriately; do not imply account or multi-user features until authentication and storage exist.
- Replace generic Streamlit defaults with consistent component styling and responsive page composition.

### 2 — Adaptive data understanding
- Detect file format, encoding, delimiter, sheet selection, header row, duplicate columns, and malformed records with actionable diagnostics.
- Detect semantic roles beyond primitive dtypes: measures, dimensions, identifiers, dates, percentages, currency-like values, coordinates, durations, and likely geographic fields.
- Show a reviewable schema map. Allow users to correct inferred roles and units.
- Support multi-sheet workbooks, JSON records/nested objects, large-file sampling, and explicit row/column limits.
- Keep raw values and transformed values traceable; never silently overwrite source meaning.

### 3 — Analysis engine and insight quality
- Build reusable descriptive statistics: count, distinct, missingness, min/max, mean/median, quantiles, spread, skew, distributions, and robust outlier candidates.
- Discover useful comparisons, segment differences, time changes, concentration, relationships, and data-quality risks based on detected roles.
- Rank findings by strength, sample size, practical relevance, and reliability; suppress weak/noisy claims.
- Add statistical context (sample size, denominator, baseline, time window, method) to every important result.
- Separate observed facts, statistical interpretations, hypotheses, and recommendations.
- Generate targeted next questions from the actual dataset and selected analysis context.

### 4 — Interactive analysis studio
- Global filter state shared across tabs and charts; clear active-filter chips and one-click reset.
- Cross-filtering and drill-down from chart marks into exact source records.
- Selectable dimensions/measures, aggregation, sorting, Top/Bottom N, date grain, comparison periods, and chart type.
- Chart-specific controls, zoom, hover detail, download image/data, and accessible data-table alternatives.
- Recommend charts based on data shape while allowing manual override.

### 5 — Decision-ready reports and exports
- Polished report with executive summary, key metrics, findings, charts, caveats, data quality, and recommended follow-up actions.
- Export PDF/HTML/XLSX/CSV/JSON where supported, with consistent formatting and provenance.
- Include report title, date range, filters, selected metrics, workspace identity, and source filename.
- Verify exports with tests and make downloads reproducible.

### 6 — Genuine AI assistance (separate, optional capability)
- Only call the product generative-AI-powered after a real model integration exists.
- Ground AI explanations in computed evidence, cite exact columns/rows/metrics, and distinguish inference from fact.
- Provide a deterministic no-AI mode; handle provider failures and cost limits transparently.
- Never send uploaded data to an external model without explicit user consent and clear privacy disclosure.

### 7 — Product operations and commercial readiness
- Settings for appearance, locale, number/date formats, analysis defaults, and privacy controls.
- Authentication, saved projects, persistent storage, team roles, and audit history only after secure architecture is selected.
- Onboarding sample datasets, guided first analysis, contextual help, and useful empty states.
- Pricing/plan limits and payment integration only after a viable no-cost deployment and support model are established.
- Security review, dependency updates, error monitoring, deployment verification, and backup/retention policy before paid customer data is accepted.

## Delivery sequence
1. Reliability: fix the live-breaking chart bug and add regression tests.
2. UX foundation: navigation, visual system, workspace settings, responsive interaction.
3. Adaptive engine: richer schema understanding and validated analysis primitives.
4. Insight studio: evidence-ranked findings, global filters, drill-down and comparisons.
5. Reports: professional exports and reproducibility.
6. AI assistance and commercial readiness: only after privacy, grounding, and deployment constraints are solved.

## Explicit non-goals for early releases
- Do not label rules/statistics as generative AI.
- Do not claim universal support for arbitrary files without limits and diagnostics.
- Do not fabricate data, business context, currency, causality, or forecasts.
- Do not expose account, team, cloud storage, or payment features as available before implemented and secured.
