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


# --- RQ3 additions ---
# Authoritative CESOP region mapping, verified against JQC scripts/07_bajio_regional_clusters.py
# All 32 states, 5 regions, complete partition (2,478 munis total).
CESOP_REGION_BY_CVE_ENT: dict[int, str] = {
    1: "Centro-Norte", 2: "Norte", 3: "Norte-Occidente", 4: "Sur",
    5: "Norte", 6: "Centro-Norte", 7: "Sur", 8: "Norte",
    9: "Centro", 10: "Norte-Occidente", 11: "Centro", 12: "Sur",
    13: "Centro", 14: "Centro-Norte", 15: "Centro", 16: "Centro-Norte",
    17: "Centro", 18: "Norte-Occidente", 19: "Norte", 20: "Sur",
    21: "Centro", 22: "Centro", 23: "Sur", 24: "Centro-Norte",
    25: "Norte-Occidente", 26: "Norte", 27: "Sur", 28: "Norte",
    29: "Centro", 30: "Sur", 31: "Sur", 32: "Norte-Occidente",
}

CESOP_REGIONS: list[str] = [
    "Norte", "Norte-Occidente", "Centro-Norte", "Centro", "Sur",
]

# Year pairs for RQ3 tests: primary 2015-vs-2025, supplementary 2015-vs-2019 and 2019-vs-2025.
RQ3_YEAR_PAIRS: list[tuple[int, int]] = [(2015, 2025), (2015, 2019), (2019, 2025)]
RQ3_PRIMARY_YEAR_PAIR: tuple[int, int] = (2015, 2025)

# Minimum expected-cell-count threshold below which Fisher-Freeman-Halton is preferred over chi-squared
FFH_MIN_EXPECTED: float = 5.0


# --- RQ3 monthly rate constants ---
RATE_SCALE: int = 100_000  # rates expressed per 100k population

# Small-denominator flagging: any (region × band) cell with fewer than this many
# munis is flagged for transparency in rate-ratio and monthly-rate outputs.
SMALL_DENOM_N_MUNIS: int = 3


# Bajio-corridor 29-muni SUN-based list (Medina-Fernandez et al. 2023; SUN 2018).
# Source: data/external/bajio_corridor_municipalities.csv — 10 ZM metropolitanas +
# 4 conurbaciones = 14 urban entities across 5 states (Ags, Gto, Mich, Qro, SLP).
# This is the paper-α canonical "narrow" Bajio definition; the 200-muni `is_bajio`
# flag in JQC's municipality_classification_v2.csv is the "broad" state-level
# corridor used for JQC's spatial-cluster contiguity work.
BAJIO_29_CVEGEOS: list[str] = [
    "01001", "01005", "01011",  # Aguascalientes (3)
    "11003", "11005", "11007", "11009", "11011", "11015", "11017",
    "11020", "11021", "11023", "11025", "11027", "11031", "11037",
    "11041", "11044",           # Guanajuato (16)
    "16069",                    # Michoacan (1)
    "22006", "22008", "22011", "22014", "22016",  # Queretaro (5)
    "24011", "24024", "24028", "24035",           # San Luis Potosi (4)
]
