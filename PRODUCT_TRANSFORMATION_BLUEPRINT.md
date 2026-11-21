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


## Implementation checkpoint — Professional Studio foundation

The first UX foundation release implements:
- A named application workspace with dedicated Overview, Analysis Studio, Data Explorer, Reports and Settings destinations.
- Session-local workspace naming, mark/initials, accent palette, light/dark theme and density controls.
- Excel worksheet selection, global category filters, field-role review and overrides.
- Adaptive recommendations and evidence-backed findings recalculated against the active filter.
- Interactive chart choices, descriptive statistics, source-row exploration and HTML/XLSX/CSV/JSON outputs.
- Reusable tested statistical helpers for numeric distributions, category shares, correlations and evidence findings.

This is a foundation, not completion of the full transformation. Remaining high-value work includes true chart-to-table cross-filtering, richer semantic typing (currency-like values, percentages, coordinates, durations), robust large-file sampling and diagnostics, multi-level JSON support, polished PDF output, accessibility and deployment verification. Authentication, persistent projects, shared teams and external AI remain explicitly out of scope until secure storage, privacy and cost architecture are implemented.


## Implementation checkpoint — Chart selection and source drill-down

The follow-up interaction layer adds Plotly point selection to group comparisons, category composition and numeric relationship charts. Selected categories/points are resolved back to the filtered source dataframe, displayed as records and offered as CSV exports. Selection parsing is isolated in tested helpers to handle missing, duplicate and malformed event fields safely.

Remaining work: coordinated cross-filter state across multiple charts, time-window brush selection, advanced semantic roles and robust large-file workflows.


## Implementation checkpoint — Semantic field understanding

A separate semantic inference layer now labels likely percentages, currency-like amounts, durations, latitude/longitude, booleans, URLs, email/phone identifiers, postal codes and high-cardinality text. It includes confidence and rationale, and deliberately leaves currency, percentage scale and coordinate reference systems unassumed. The detected semantic metadata is displayed in the field dictionary and is covered by focused tests, including false-positive name checks.

Remaining work: user-editable units and semantic types, locale-aware numeric parsing, nested JSON and multi-header diagnostics, and stronger domain-specific analysis templates.


## Implementation checkpoint — Functional workspace controls

Workspace settings now include an optional uploaded logo (session-only), workspace name/subtitle, mark/initials, four accent palettes, light/dark theme, density, default analysis view, Top N, numeric precision and a report methodology toggle. These controls are wired to the interface and report generation rather than being decorative settings. Reset runs through a safe session-state callback.

Persistent settings, cloud identity and cross-device logo storage remain intentionally unimplemented until a secure account/storage layer exists.


## Implementation checkpoint — Evidence-ranked segment discovery

The insight engine now compares numeric measures across categorical segments. It reports group medians against the overall baseline, includes valid sample sizes and suppresses comparisons where groups are too small. The explanation explicitly labels the result as descriptive rather than causal. Regression tests cover both a material difference and a tiny-group case.

Next: time-window change detection with comparison baselines, multiple-testing safeguards, richer distribution shape diagnostics and user-controlled insight thresholds.
