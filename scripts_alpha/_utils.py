from __future__ import annotations
import polars as pl

BAND_ORDER: list[str] = [
    "community", "rural", "semi_urban", "small_city",
    "medium_city", "city", "large_city",
]

BAND_CUTPOINTS: list[tuple[str, int, int]] = [
    ("community",   0,         2_500),
    ("rural",       2_500,     15_000),
    ("semi_urban",  15_000,    50_000),
    ("small_city",  50_000,    150_000),
    ("medium_city", 150_000,   500_000),
    ("city",        500_000,   1_000_000),
    ("large_city",  1_000_000, 10**12),
]

STATUS_ORDER: list[str] = ["not_located", "located_alive", "located_dead"]

STATUS_ID_MAP: dict[int, str] = {
    7: "not_located",
    2: "located_alive",
    3: "located_dead",
}

CROSS_SECTION_YEARS: list[int] = [2015, 2019, 2025]

# Per DiB Table 2: 5-char zero-padded cve_geo ending in "998" (no muni
# reference / unknown state 99998) or "999" (muni unknown / unresolved
# state 99999) is a sentinel.
SENTINEL_SUFFIXES: tuple[str, str] = ("998", "999")


def pivot_ordered(df: pl.DataFrame, *, index, on, values,
                  column_order: list[str],
                  aggregate_function=None) -> pl.DataFrame:
    """Pivot then enforce deterministic column order. Fills missing
    columns with nulls so table shape is stable across reruns."""
    kwargs = dict(index=index, on=on, values=values)
    if aggregate_function is not None:
        kwargs["aggregate_function"] = aggregate_function
    w = df.pivot(**kwargs)
    for c in column_order:
        if c not in w.columns:
            w = w.with_columns(pl.lit(None).alias(c))
    idx_cols = index if isinstance(index, list) else [index]
    return w.select(idx_cols + column_order)


# --- RQ1 additions ---
WILSON_ALPHA: float = 0.05


def wilson_ci(k: int, n: int, alpha: float = WILSON_ALPHA) -> tuple[float, float]:
    """Wilson score 95% CI for a binomial proportion.

    Hand-rolled, no SciPy dependency. Returns (lo, hi) bounded in [0, 1].
    Returns (nan, nan) if n == 0.
    """
    from math import sqrt, nan
    if n == 0:
        return (nan, nan)
    # Normal-approx critical value for alpha=0.05 -> 1.959963984540054
    # Compute from scipy if available for arbitrary alpha; hand-code 0.05
    # for the default call path to avoid an import in hot loops.
    if alpha == 0.05:
        z = 1.959963984540054
    else:
        from scipy.stats import norm
        z = norm.ppf(1 - alpha / 2)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


# --- RQ2 additions ---
CED_STATES: list[tuple[int, str, str]] = [
    (14, "Jalisco",         "Centro-Norte"),
    (11, "Guanajuato",      "Centro"),
    (5,  "Coahuila",        "Norte"),
    (30, "Veracruz",        "Sur"),
    (18, "Nayarit",         "Norte-Occidente"),
    (27, "Tabasco",         "Sur"),
    (19, "Nuevo Leon",      "Norte"),
    (15, "Edo. de Mexico",  "Centro"),
]

TRAJECTORY_CLASSES: list[str] = [
    "Accelerating", "Peak-decline", "Moderate", "Low-baseline",
]
# "Female-anomalous" is an orthogonal Boolean flag, NOT a mutually-exclusive class.
