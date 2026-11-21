from __future__ import annotations

import math
import pandas as pd


def _clean_series(trend: pd.DataFrame) -> pd.DataFrame:
    required = {"period", "value"}
    if not required.issubset(trend.columns):
        raise ValueError("Time series must contain period and value columns.")
    work = trend.loc[:, ["period", "value"]].copy()
    work["period"] = pd.to_datetime(work["period"], errors="coerce")
    work["value"] = pd.to_numeric(work["value"], errors="coerce")
    work = work.dropna(subset=["period", "value"])
    work = work[work["value"].map(lambda x: math.isfinite(float(x)))]
    if work.empty:
        return pd.DataFrame(columns=["period", "value"])
    # Multiple observations for one displayed period are combined transparently.
    return work.groupby("period", as_index=False)["value"].mean().sort_values("period").reset_index(drop=True)


def _expected_frequency(periods: pd.Series) -> str | None:
    dates = pd.DatetimeIndex(periods.dropna().sort_values().unique())
    if len(dates) < 3:
        return None
    median_days = float(pd.Series(dates[1:] - dates[:-1]).dt.total_seconds().median() / 86400)
    if 0.8 <= median_days <= 1.2:
        return "D"
    if 5.5 <= median_days <= 8.5:
        return "W"
    if 25 <= median_days <= 35:
        return "MS"
    if 80 <= median_days <= 100:
        return "QS"
    if 350 <= median_days <= 380:
        return "YS"
    return None


def analyze_time_series(
    trend: pd.DataFrame,
    min_periods: int = 6,
    change_threshold: float = 3.5,
) -> dict:
    """Return evidence-led trend diagnostics without forecasting or causal claims."""
    if min_periods < 4:
        raise ValueError("min_periods must be at least 4.")
    if change_threshold <= 0:
        raise ValueError("change_threshold must be positive.")

    clean = _clean_series(trend)
    empty = clean.empty
    if empty:
        return {
            "series": clean.assign(change=pd.Series(dtype=float), change_pct=pd.Series(dtype=float)),
            "findings": [],
            "valid_periods": 0,
            "missing_periods": None,
            "frequency": None,
            "eligible_for_comparison": False,
        }

    clean["change"] = clean["value"].diff()
    previous = clean["value"].shift(1)
    clean["change_pct"] = (clean["change"] / previous.abs().where(previous.abs() > 1e-12)) * 100

    frequency = _expected_frequency(clean["period"])
    missing_periods = None
    if frequency:
        expected = pd.date_range(clean["period"].min(), clean["period"].max(), freq=frequency)
        observed = pd.DatetimeIndex(clean["period"])
        missing_periods = int(len(expected.difference(observed)))

    findings: list[dict[str, str]] = []
    n = len(clean)
    if missing_periods:
        findings.append({
            "kind": "coverage",
            "title": f"{missing_periods:,} missing time period(s)",
            "detail": f"The observed series appears to follow a {frequency} cadence, but {missing_periods:,} expected period(s) have no valid value. Missing periods are not treated as zero.",
            "action": "Check source coverage and whether records were omitted",
        })

    if n >= min_periods:
        midpoint = n // 2
        first_median = float(clean["value"].iloc[:midpoint].median())
        second_median = float(clean["value"].iloc[midpoint:].median())
        baseline = max(abs(first_median), abs(second_median), 1e-9)
        relative = (second_median - first_median) / baseline * 100
        if abs(relative) >= 15:
            direction = "higher" if relative > 0 else "lower"
            findings.append({
                "kind": "trend shift",
                "title": f"Later-period median is {abs(relative):.1f}% {direction}",
                "detail": f"The median across the later half is {second_median:,.3f}, versus {first_median:,.3f} in the earlier half ({relative:+.1f}% using the larger absolute median as denominator). This is a descriptive comparison, not a forecast or causal explanation.",
                "action": "Compare the two time windows and inspect the underlying records",
            })

        changes = clean["change"].dropna()
        if len(changes) >= min_periods - 1:
            center = float(changes.median())
            mad = float((changes - center).abs().median())
            robust_scale = 1.4826 * mad
            if robust_scale > 1e-12:
                scores = (changes - center).abs() / robust_scale
                flagged = scores[scores >= change_threshold]
            else:
                deviations = (changes - center).abs()
                typical = float(deviations[deviations > 1e-12].median()) if (deviations > 1e-12).any() else 0.0
                flagged = deviations[deviations >= max(1e-9, typical * change_threshold)] if typical else deviations.iloc[0:0]
            if not flagged.empty:
                positions = [int(clean.index.get_loc(idx)) for idx in flagged.index]
                examples = [clean.iloc[pos]["period"].strftime("%Y-%m-%d") for pos in positions[:3]]
                findings.append({
                    "kind": "change anomaly",
                    "title": f"{len(flagged):,} unusually large period-to-period change(s)",
                    "detail": f"Robust median/MAD screening flagged changes around {', '.join(examples)}. These are review signals; they may reflect real events, sparse data or data-quality issues.",
                    "action": "Inspect the flagged periods and verify source records",
                })
    else:
        findings.append({
            "kind": "coverage",
            "title": "More periods are needed for reliable time comparisons",
            "detail": f"Only {n:,} valid periods are available; at least {min_periods} are required for the time-shift and change-anomaly checks. No trend conclusion is made.",
            "action": "Add more historical periods or use the descriptive series view",
        })

    return {
        "series": clean,
        "findings": findings,
        "valid_periods": int(n),
        "missing_periods": missing_periods,
        "frequency": frequency,
        "eligible_for_comparison": n >= min_periods,
    }
