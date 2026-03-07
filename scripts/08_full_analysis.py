"""
Full RNPDNO spatial analysis.

Steps:
  1. Fix Bajío list (6 corrections, 4 removals) → 205 municipalities
  2. Build municipality_classification_v2 (region, is_bajio, pop_band)
  3. For each status × metric (rates|cases) × year: LISA → HH clusters
  4. Aggregate: Norte vs Bajío trend, band composition, Jaccard rates vs cases
  5. Figure

Outputs:
  data/processed/bajio_cvegeo_list_v2.csv
  data/processed/municipality_classification_v2.csv
  data/processed/hh_clusters_rates_{status}.csv
  data/processed/hh_clusters_cases_{status}.csv
  data/processed/cluster_comparison_rates_vs_cases.csv
  reports/figures/fig_rates_vs_cases_hh.pdf
"""

import sys
import warnings
from collections import Counter
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import unicodedata

sys.path.insert(0, str(Path.cwd()))
from rnpdno_eda.models.spatial import load_municipios, build_queen_weights, run_lisa

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

YEARS = list(range(2015, 2025))
MIN_CLUSTER = 3
PERMUTATIONS = 999
ALPHA = 0.05

REGION_MAP = {
    "Norte":           [2, 5, 8, 19, 26, 28],
    "Norte-Occidente": [3, 10, 18, 25, 32],
    "Centro-Norte":    [1, 6, 14, 16, 24],
    "Centro":          [9, 11, 13, 15, 17, 21, 22, 29],
    "Sur":             [4, 7, 12, 20, 23, 27, 30, 31],
}
CVE_TO_REGION = {c: r for r, cves in REGION_MAP.items() for c in cves}

STATUSES = {
    "total":                 "data/raw/rnpdno_total.csv",
    "disappeared":           "data/raw/rnpdno_disappeared_not_located.csv",
    "located_alive":         "data/raw/rnpdno_located_alive.csv",
    "located_dead":          "data/raw/rnpdno_located_dead.csv",
}

BAND_LABELS = {
    5: "Band 5: Millonarias",
    4: "Band 4: Metropolitan",
    3: "Band 3: Mid-Size",
    2: "Band 2: Small Town",
    1: "Band 1: Rural",
}

REGION_COLORS = {
    "Norte": "#D62728",
    "Norte-Occidente": "#FF7F0E",
    "Centro-Norte": "#2CA02C",
    "Centro": "#1F77B4",
    "Sur": "#9467BD",
}

# ---------------------------------------------------------------------------
# Bajío municipality list (corrected: 6 fixes, 4 removals → 205)
# ---------------------------------------------------------------------------

BAJIO_MUNIS = {
    1: None,   # ALL Aguascalientes (11)
    11: None,  # ALL Guanajuato (46)
    22: None,  # ALL Querétaro (18)
    14: [      # Jalisco (54 → corrected names)
        "Acatic", "Arandas", "Cañadas de Obregón", "Encarnación de Díaz",
        "Jalostotitlán", "Jesús María", "Lagos de Moreno", "Mexticacán",
        "Ojuelos de Jalisco", "San Diego de Alejandría", "San Juan de los Lagos",
        "San Julián", "San Miguel el Alto", "Teocaltiche", "Tepatitlán de Morelos",
        "Unión de San Antonio", "Valle de Guadalupe", "Villa Hidalgo",
        "Atotonilco el Alto", "Ayotlán", "Degollado", "Jamay", "La Barca",
        "Ocotlán", "Poncitlán", "Tototlán", "Zapotlán del Rey",
        "Amatitán", "El Arenal", "Magdalena", "San Juanito de Escobedo",
        "Tequila", "Teuchitlán",
        "Guadalajara", "Zapopan", "San Pedro Tlaquepaque",  # FIX: Tlaquepaque→San Pedro Tlaquepaque
        "Tonalá", "Tlajomulco de Zúñiga", "El Salto", "Juanacatlán",
        "Ixtlahuacán de los Membrillos",
        "Ameca", "Cocula", "Etzatlán", "Hostotipaquillo", "San Marcos",
        "Tala", "Ahualulco de Mercado", "Zapotlanejo", "Cuquío",
    ],
    16: [      # Michoacán (34 → removed Villa Jiménez, Villa Morelos → 32)
        "Álvaro Obregón", "Angamacutiro", "Angangueo", "Churintzio", "Cuitzeo",
        "Ecuandureo", "Huaniqueo", "Indaparapeo", "Irimbo", "Jiménez",
        "José Sixto Verduzco", "Lagunillas", "La Piedad", "Maravatío", "Morelia",
        "Morelos", "Panindícuaro", "Penjamillo", "Purépero", "Puruándiro",
        "Queréndaro", "Santa Ana Maya", "Senguio", "Tangancícuaro", "Tanhuato",
        "Tarímbaro", "Tlalpujahua", "Tlazazalca", "Tuxpan",  # removed Villa Jiménez, Villa Morelos
        "Yurécuaro", "Zináparo", "Zacapu",
    ],
    24: [      # SLP (15 → removed Escalerillas → 14; 2 name fixes)
        "Ahualulco del Sonido 13",    # FIX: Ahualulco→Ahualulco del Sonido 13
        "Armadillo de los Infante", "Cerro de San Pedro",
        "Guadalcázar", "Mexquitic de Carmona", "Moctezuma", "San Luis Potosí",
        "Santa María del Río", "Soledad de Graciano Sánchez", "Villa de Arriaga",
        "Villa de Reyes", "Villa Hidalgo",
        "Zaragoza",                   # FIX: Villa de Zaragoza→Zaragoza
        "Villa Juárez",
        # removed Escalerillas (locality, not municipality)
    ],
    32: [      # Zacatecas (31 → removed Pánfilo Natera → 30; 3 name fixes)
        "Apozol", "Apulco", "Atolinga", "Benito Juárez", "Calera",
        "Cañitas de Felipe Pescador", "Chalchihuites", "Cuauhtémoc",
        "El Plateado de Joaquín Amaro",
        "Benito Juárez",              # FIX: Florencia de Benito Juárez→Benito Juárez (dup→deduplicated later)
        "Fresnillo", "Genaro Codina", "General Enrique Estrada",
        "General Pánfilo Natera", "Guadalupe", "Huanusco", "Jalpa", "Jerez",
        "Juchipila", "Luis Moya", "Momax",
        "Nochistlán de Mejía",        # FIX: Nochistlán→Nochistlán de Mejía
        "Noria de Ángeles",
        "Ojocaliente",
        # removed Pánfilo Natera (duplicate of General Pánfilo Natera)
        "Tabasco", "Tepechitlán",
        "Teúl de González Ortega",
        "Tlaltenango de Sánchez Román",  # FIX: Tlaltenango→Tlaltenango de Sánchez Román
        "Trancoso", "Zacatecas",
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def strip_accents(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", str(s))
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn").lower().strip()


def assign_pop_band(pop: float) -> int:
    if pd.isna(pop):
        return 0
    if pop >= 1_000_000:
        return 5
    if pop >= 500_000:
        return 4
    if pop >= 100_000:
        return 3
    if pop >= 25_000:
        return 2
    return 1


def connected_components(nodes: set, adjacency: dict) -> list[list]:
    visited = set()
    components = []
    for start in nodes:
        if start in visited:
            continue
        comp = []
        queue = [start]
        visited.add(start)
        while queue:
            curr = queue.pop(0)
            comp.append(curr)
            for nbr in adjacency.get(curr, []):
                if nbr in nodes and nbr not in visited:
                    visited.add(nbr)
                    queue.append(nbr)
        components.append(comp)
    return components


# ---------------------------------------------------------------------------
# STEP 1 & 2: Classification table
# ---------------------------------------------------------------------------

def build_classification():
    print("=" * 60)
    print("STEP 1-2: Building municipality classification table")
    print("=" * 60)

    # Load AGEEML (latin-1, original INEGI encoding)
    ageeml = pd.read_csv("data/external/ageeml_catalog.csv", encoding="latin-1")
    ageeml["cvegeo"] = ageeml["CVEGEO"].astype(str).str.zfill(5)
    ageeml["cve_ent_int"] = ageeml["CVE_ENT"].astype(int)
    ageeml["nom_norm"] = ageeml["NOM_MUN"].apply(strip_accents)
    ageeml["region"] = ageeml["cve_ent_int"].map(CVE_TO_REGION)

    # --- Population bands from CONAPO 2020 ---
    pop = pd.read_parquet("data/external/conapo_poblacion_1990_2070.parquet")
    pop["cvegeo"] = pop["cve_geo"].astype(str).str.zfill(5)
    pop2020 = pop[pop["year"] == 2020][["cvegeo", "pob_total"]].copy()
    pop2020["pop_band"] = pop2020["pob_total"].apply(assign_pop_band)
    pop_lookup = pop2020.set_index("cvegeo")["pop_band"].to_dict()

    ageeml["pop_band"] = ageeml["cvegeo"].map(pop_lookup).fillna(0).astype(int)

    # --- Bajío matching ---
    ageeml["is_bajio"] = False
    all_bajio_states = [k for k, v in BAJIO_MUNIS.items() if v is None]
    ageeml.loc[ageeml["cve_ent_int"].isin(all_bajio_states), "is_bajio"] = True
    n_all = ageeml["is_bajio"].sum()
    print(f"  ALL-state Bajío (states {all_bajio_states}): {n_all} municipalities")

    unmatched = []
    n_partial = 0
    for cve_ent, names in BAJIO_MUNIS.items():
        if names is None:
            continue
        subset = ageeml[ageeml["cve_ent_int"] == cve_ent]
        norm_map = dict(zip(subset["nom_norm"], subset["cvegeo"]))
        seen_cvegeos = set()
        for name in names:
            norm = strip_accents(name)
            if norm in norm_map:
                cvegeo = norm_map[norm]
                if cvegeo not in seen_cvegeos:  # deduplicate Zacatecas "Benito Juárez"
                    ageeml.loc[ageeml["cvegeo"] == cvegeo, "is_bajio"] = True
                    seen_cvegeos.add(cvegeo)
                    n_partial += 1
            else:
                # Try startswith fallback for partial name variants
                matches = [cv for nm, cv in norm_map.items() if nm.startswith(norm[:8])]
                if not matches:
                    unmatched.append((cve_ent, name))

    total_bajio = ageeml["is_bajio"].sum()
    total_listed = n_all + n_partial
    print(f"\n  BAJÍO MATCH RATE: {total_bajio}/205 ({100 * total_bajio / 205:.1f}%)")
    if unmatched:
        print(f"  UNMATCHED ({len(unmatched)}):")
        for cve, name in unmatched:
            print(f"    CVE_ENT={cve:02d}: '{name}'")
    else:
        print("  All Bajío municipalities matched.")

    # Save bajio list
    bajio_df = (
        ageeml[ageeml["is_bajio"]][["cvegeo", "NOM_MUN", "CVE_ENT"]]
        .rename(columns={"NOM_MUN": "nom_mun", "CVE_ENT": "cve_estado"})
        .sort_values("cvegeo")
        .reset_index(drop=True)
    )
    bajio_df.to_csv("data/processed/bajio_cvegeo_list_v2.csv", index=False)
    print(f"\n  Saved: bajio_cvegeo_list_v2.csv ({len(bajio_df)} rows)")

    # Save classification
    clf = ageeml[["cvegeo", "region", "is_bajio", "pop_band"]].sort_values("cvegeo").reset_index(drop=True)
    clf.to_csv("data/processed/municipality_classification_v2.csv", index=False)
    print(f"  Saved: municipality_classification_v2.csv ({len(clf)} rows)")
    print(f"\n  Band distribution (2020 population):")
    print(clf["pop_band"].map(lambda b: BAND_LABELS.get(b, "Unknown")).value_counts().to_string())
    print(f"\n  Region distribution:")
    print(clf["region"].value_counts().to_string())

    return clf


# ---------------------------------------------------------------------------
# STEP 2b: Annual population per municipality (for rate computation)
# ---------------------------------------------------------------------------

def build_pop_reference() -> pd.DataFrame:
    """Returns DataFrame: cvegeo × year → pop_total + pop_band."""
    pop = pd.read_parquet("data/external/conapo_poblacion_1990_2070.parquet")
    pop["cvegeo"] = pop["cve_geo"].astype(str).str.zfill(5)
    pop = pop[(pop["year"] >= 2015) & (pop["year"] <= 2024)][["cvegeo", "year", "pob_total"]].copy()
    pop["pop_band"] = pop["pob_total"].apply(assign_pop_band)
    return pop.set_index(["cvegeo", "year"])


# ---------------------------------------------------------------------------
# STEP 3: Annual panels per status file
# ---------------------------------------------------------------------------

def build_annual_panel(status_file: str, pop_ref: pd.DataFrame, id_order: list) -> pd.DataFrame:
    """
    Returns DataFrame indexed by (cvegeo, year) with columns:
      cases, rate, pop_band
    All municipalities in id_order are present; missing ones get 0.
    """
    raw = pd.read_csv(status_file, dtype={"cvegeo": str})
    raw["cvegeo"] = raw["cvegeo"].str.zfill(5)

    annual_cases = (
        raw[raw["year"].between(2015, 2024)]
        .groupby(["cvegeo", "year"])["total"]
        .sum()
        .rename("cases")
        .reset_index()
    )

    # Full grid: all municipalities × all years
    all_cvegeos = pd.Series(id_order, name="cvegeo")
    all_years = pd.Series(YEARS, name="year")
    grid = all_cvegeos.to_frame().merge(all_years.to_frame(), how="cross")

    panel = grid.merge(annual_cases, on=["cvegeo", "year"], how="left").fillna({"cases": 0})

    # Join population
    panel = panel.join(pop_ref[["pob_total", "pop_band"]], on=["cvegeo", "year"])

    panel["rate"] = np.where(
        panel["pob_total"] > 0,
        panel["cases"] / panel["pob_total"] * 100_000,
        0.0,
    )
    panel["rate"] = panel["rate"].replace([np.inf, -np.inf], 0).fillna(0)
    panel["cases"] = panel["cases"].fillna(0)

    return panel.set_index(["cvegeo", "year"])


# ---------------------------------------------------------------------------
# STEP 4: Cluster extraction
# ---------------------------------------------------------------------------

def extract_clusters(
    hh_set: set,
    adjacency: dict,
    clf_lookup: dict,      # cvegeo → {region, is_bajio, pop_band}
    pop_band_year: dict,   # cvegeo → pop_band for this year
    centroids: pd.DataFrame,
    year: int,
    status: str,
    metric: str,
) -> list[dict]:
    components = connected_components(hh_set, adjacency)
    valid = [c for c in components if len(c) >= MIN_CLUSTER]
    rows = []
    for idx, comp in enumerate(valid):
        regions = [clf_lookup[cv]["region"] for cv in comp if cv in clf_lookup]
        bajio_flags = [clf_lookup[cv]["is_bajio"] for cv in comp if cv in clf_lookup]
        bands = [pop_band_year.get(cv, clf_lookup.get(cv, {}).get("pop_band", 0)) for cv in comp]

        dom_region = Counter(regions).most_common(1)[0][0] if regions else "Unknown"
        pct_bajio = sum(bajio_flags) / len(bajio_flags) if bajio_flags else 0.0
        dom_band = Counter(b for b in bands if b > 0).most_common(1)[0][0] if any(b > 0 for b in bands) else 0

        lons = [centroids.loc[cv, "centroid_lon"] for cv in comp if cv in centroids.index]
        lats = [centroids.loc[cv, "centroid_lat"] for cv in comp if cv in centroids.index]

        rows.append({
            "year": year,
            "status": status,
            "metric": metric,
            "cluster_id": f"{year}_{status}_{metric}_{idx + 1:03d}",
            "n_munis": len(comp),
            "region": dom_region,
            "pct_bajio": round(pct_bajio, 4),
            "is_bajio_cluster": pct_bajio >= 0.5,
            "dominant_band": dom_band,
            "band_label": BAND_LABELS.get(dom_band, "Unknown"),
            "centroid_x": round(float(np.mean(lons)), 6) if lons else np.nan,
            "centroid_y": round(float(np.mean(lats)), 6) if lats else np.nan,
        })
    return rows


# ---------------------------------------------------------------------------
# STEP 5: Main LISA loop
# ---------------------------------------------------------------------------

def run_all_analyses(clf: pd.DataFrame):
    print("\n" + "=" * 60)
    print("STEP 3: LISA analyses (4 statuses × 2 metrics × 10 years)")
    print("=" * 60)

    # Spatial setup
    gdf = load_municipios()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        w = build_queen_weights(gdf)
    adjacency = w.neighbors
    id_order = w.id_order
    print(f"  Spatial weights: {len(id_order)} municipalities, {sum(len(v) for v in adjacency.values())//2} pairs")

    # Centroids
    geo_raw = gpd.read_parquet("data/external/municipios_2024.geoparquet")
    geo_raw["cvegeo"] = geo_raw["cve_geo"].astype(str).str.zfill(5)
    centroids = geo_raw.set_index("cvegeo")[["centroid_lon", "centroid_lat"]]

    # Classification lookup
    clf_lookup = {
        row.cvegeo: {"region": row.region, "is_bajio": row.is_bajio, "pop_band": row.pop_band}
        for row in clf.itertuples()
    }

    # Population reference
    pop_ref = build_pop_reference()
    # Yearly band lookup: (cvegeo, year) → pop_band
    pop_band_by_year = {
        (cv, yr): row.pop_band
        for (cv, yr), row in pop_ref.iterrows()
    }

    # Containers for all results
    all_cluster_rows = []       # all clusters, all statuses, both metrics
    comparison_rows = []        # Jaccard per year × status

    for status_name, status_file in STATUSES.items():
        print(f"\n  --- Status: {status_name} ---")
        panel = build_annual_panel(status_file, pop_ref, id_order)

        clusters_rates = []
        clusters_cases = []
        hh_sets_rates = {}   # year → set of HH cvegeos (rates)
        hh_sets_cases = {}   # year → set of HH cvegeos (cases)

        for year in YEARS:
            yr_panel = panel.xs(year, level="year") if year in panel.index.get_level_values("year") else pd.DataFrame()

            # Align to id_order
            rates_vals = yr_panel.reindex(id_order)["rate"].fillna(0).values
            cases_vals = yr_panel.reindex(id_order)["cases"].fillna(0).values

            # Pop band for this year per municipality
            pop_band_year = {cv: pop_band_by_year.get((cv, year), 0) for cv in id_order}

            # --- LISA: RATES ---
            res_r = run_lisa(rates_vals, w, permutations=PERMUTATIONS, alpha=ALPHA)
            hh_r = {id_order[i] for i, c in enumerate(res_r["clusters"]) if c == 1}
            hh_sets_rates[year] = hh_r
            rows_r = extract_clusters(hh_r, adjacency, clf_lookup, pop_band_year, centroids, year, status_name, "rates")
            clusters_rates.extend(rows_r)

            # --- LISA: CASES ---
            res_c = run_lisa(cases_vals, w, permutations=PERMUTATIONS, alpha=ALPHA)
            hh_c = {id_order[i] for i, c in enumerate(res_c["clusters"]) if c == 1}
            hh_sets_cases[year] = hh_c
            rows_c = extract_clusters(hh_c, adjacency, clf_lookup, pop_band_year, centroids, year, status_name, "cases")
            clusters_cases.extend(rows_c)

            # Jaccard(rates HH, cases HH) — raw HH sets (not cluster-filtered)
            inter = len(hh_r & hh_c)
            union = len(hh_r | hh_c)
            jaccard = inter / union if union > 0 else 0.0

            n_valid_r = len([x for x in [connected_components(hh_r, adjacency)] if x]) if hh_r else 0
            n_valid_c = len([x for x in [connected_components(hh_c, adjacency)] if x]) if hh_c else 0

            print(
                f"    {year} rates: HH={len(hh_r)}, clusters={len(rows_r)} | "
                f"cases: HH={len(hh_c)}, clusters={len(rows_c)} | "
                f"Jaccard={jaccard:.3f}"
            )

            comparison_rows.append({
                "year": year,
                "status": status_name,
                "n_hh_rates": len(hh_r),
                "n_hh_cases": len(hh_c),
                "n_clusters_rates": len(rows_r),
                "n_clusters_cases": len(rows_c),
                "jaccard_hh": round(jaccard, 4),
                "hh_intersection": inter,
                "hh_union": union,
            })

        all_cluster_rows.extend(clusters_rates)
        all_cluster_rows.extend(clusters_cases)

        # Save per-status CSVs
        pd.DataFrame(clusters_rates).to_csv(
            f"data/processed/hh_clusters_rates_{status_name}.csv", index=False
        )
        pd.DataFrame(clusters_cases).to_csv(
            f"data/processed/hh_clusters_cases_{status_name}.csv", index=False
        )
        print(f"    Saved hh_clusters_rates_{status_name}.csv ({len(clusters_rates)} clusters)")
        print(f"    Saved hh_clusters_cases_{status_name}.csv ({len(clusters_cases)} clusters)")

    # Save comparison
    comp_df = pd.DataFrame(comparison_rows)
    comp_df.to_csv("data/processed/cluster_comparison_rates_vs_cases.csv", index=False)
    print(f"\n  Saved: cluster_comparison_rates_vs_cases.csv ({len(comp_df)} rows)")

    return pd.DataFrame(all_cluster_rows), comp_df


# ---------------------------------------------------------------------------
# STEP 6: Aggregate & report
# ---------------------------------------------------------------------------

def print_summary(all_clusters: pd.DataFrame, comp_df: pd.DataFrame):
    print("\n" + "=" * 60)
    print("STEP 4: Summary statistics")
    print("=" * 60)

    from scipy import stats

    for metric in ["rates", "cases"]:
        print(f"\n  === Metric: {metric.upper()} ===")
        sub = all_clusters[(all_clusters["metric"] == metric) & (all_clusters["status"] == "total")]

        # Norte vs Bajío trend
        norte_by_yr = sub[sub["region"] == "Norte"].groupby("year")["n_munis"].sum()
        bajio_by_yr = sub[sub["is_bajio_cluster"]].groupby("year")["n_munis"].sum()

        norte_hh = [norte_by_yr.get(y, 0) for y in YEARS]
        bajio_hh = [bajio_by_yr.get(y, 0) for y in YEARS]

        sl_n, _, r_n, p_n, _ = stats.linregress(YEARS, norte_hh)
        sl_b, _, r_b, p_b, _ = stats.linregress(YEARS, bajio_hh)

        print(f"\n  Norte vs Bajío (status=total, {metric}):")
        print(f"    Year  Norte_HH  Bajío_HH")
        for y in YEARS:
            print(f"    {y}   {norte_hh[YEARS.index(y)]:7d}  {bajio_hh[YEARS.index(y)]:7d}")
        print(f"\n    Norte trend:  slope={sl_n:.2f}/yr, R²={r_n**2:.3f}, p={p_n:.4f}"
              + (" [SIGNIFICANT]" if p_n < 0.05 else ""))
        print(f"    Bajío trend:  slope={sl_b:.2f}/yr, R²={r_b**2:.3f}, p={p_b:.4f}"
              + (" [SIGNIFICANT]" if p_b < 0.05 else ""))

    # Band composition of HH clusters (status=total, rates)
    print("\n  === Band composition (status=total, rates) ===")
    band_sub = all_clusters[(all_clusters["status"] == "total") & (all_clusters["metric"] == "rates")]
    band_counts = band_sub.groupby("dominant_band")["n_munis"].sum().sort_index(ascending=False)
    total_munis = band_counts.sum()
    for band, count in band_counts.items():
        label = BAND_LABELS.get(band, "Unknown")
        print(f"    {label}: {count} munis ({100*count/total_munis:.1f}%)")

    # Jaccard summary by status
    print("\n  === Jaccard (rates vs cases) by status ===")
    jac_summary = comp_df.groupby("status")["jaccard_hh"].agg(["mean", "min", "max"])
    print(jac_summary.to_string())

    # 2015 vs 2024 comparison
    print("\n  === Norte vs Bajío: 2015 vs 2024 (status=total, rates) ===")
    sub_r = all_clusters[(all_clusters["metric"] == "rates") & (all_clusters["status"] == "total")]
    for yr in [2015, 2024]:
        n_c = sub_r[(sub_r["year"] == yr) & (sub_r["region"] == "Norte")]
        b_c = sub_r[(sub_r["year"] == yr) & sub_r["is_bajio_cluster"]]
        print(
            f"  {yr}: Norte={len(n_c)} clusters ({n_c['n_munis'].sum()} munis) | "
            f"Bajío={len(b_c)} clusters ({b_c['n_munis'].sum()} munis)"
        )


# ---------------------------------------------------------------------------
# STEP 7: Figure
# ---------------------------------------------------------------------------

def make_figure(all_clusters: pd.DataFrame, comp_df: pd.DataFrame):
    print("\n" + "=" * 60)
    print("STEP 5: Figure")
    print("=" * 60)

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle(
        "RNPDNO Spatial Clusters: Rates vs Cases | Norte vs Bajío | 2015–2024",
        fontsize=13, fontweight="bold"
    )

    # Panels A & B: Norte + Bajío cluster count by year — rates vs cases (status=total)
    for col_idx, metric in enumerate(["rates", "cases"]):
        ax = axes[0, col_idx]
        sub = all_clusters[(all_clusters["status"] == "total") & (all_clusters["metric"] == metric)]

        norte_n = [len(sub[(sub["year"] == y) & (sub["region"] == "Norte")]) for y in YEARS]
        bajio_n = [len(sub[(sub["year"] == y) & sub["is_bajio_cluster"]]) for y in YEARS]

        ax.plot(YEARS, norte_n, "o-", color=REGION_COLORS["Norte"], label="Norte", lw=2)
        ax.plot(YEARS, bajio_n, "s--", color="#E377C2", label="Bajío", lw=2)
        ax.set_title(f"A{col_idx+1}. HH Clusters — {metric.upper()} (total)", fontweight="bold")
        ax.set_xlabel("Year")
        ax.set_ylabel("Number of spatial clusters (≥3 munis)")
        ax.legend(fontsize=8)
        ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
        ax.grid(alpha=0.3)

    # Panel C: Jaccard heatmap by status × year (rates vs cases)
    ax = axes[0, 2]
    status_list = list(STATUSES.keys())
    jac_matrix = np.zeros((len(status_list), len(YEARS)))
    for i, st in enumerate(status_list):
        for j, yr in enumerate(YEARS):
            row = comp_df[(comp_df["status"] == st) & (comp_df["year"] == yr)]
            jac_matrix[i, j] = row["jaccard_hh"].values[0] if len(row) else 0.0

    im = ax.imshow(jac_matrix, aspect="auto", cmap="RdYlGn", vmin=0, vmax=1)
    ax.set_xticks(range(len(YEARS)))
    ax.set_xticklabels(YEARS, rotation=45, ha="right", fontsize=7)
    ax.set_yticks(range(len(status_list)))
    ax.set_yticklabels(status_list, fontsize=8)
    plt.colorbar(im, ax=ax, fraction=0.046)
    ax.set_title("C. Jaccard (Rates vs Cases HH)", fontweight="bold")

    # Panel D: Cluster count by region, status=total, rates (stacked bar)
    ax = axes[1, 0]
    sub_r = all_clusters[(all_clusters["status"] == "total") & (all_clusters["metric"] == "rates")]
    regions = list(REGION_MAP.keys())
    bottom = np.zeros(len(YEARS))
    for region in regions:
        vals = [len(sub_r[(sub_r["year"] == y) & (sub_r["region"] == region)]) for y in YEARS]
        ax.bar(YEARS, vals, bottom=bottom, color=REGION_COLORS[region], label=region, alpha=0.85)
        bottom += np.array(vals, dtype=float)
    ax.set_title("D. Clusters by Region (rates, total)", fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("Clusters (≥3 munis)")
    ax.legend(fontsize=7, loc="upper left")
    ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
    ax.grid(axis="y", alpha=0.3)

    # Panel E: Band composition of HH clusters (rates, total)
    ax = axes[1, 1]
    band_colors = {5: "#7B2D8B", 4: "#1F77B4", 3: "#2CA02C", 2: "#FF7F0E", 1: "#D62728", 0: "#999999"}
    sub_r2 = all_clusters[(all_clusters["status"] == "total") & (all_clusters["metric"] == "rates")]
    bottom = np.zeros(len(YEARS))
    for band in [5, 4, 3, 2, 1]:
        vals = [
            sub_r2[(sub_r2["year"] == y) & (sub_r2["dominant_band"] == band)]["n_munis"].sum()
            for y in YEARS
        ]
        ax.bar(YEARS, vals, bottom=bottom, color=band_colors[band],
               label=BAND_LABELS[band].split(": ")[1], alpha=0.85)
        bottom += np.array(vals, dtype=float)
    ax.set_title("E. HH Munis by Pop Band (rates, total)", fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("Municipalities in HH clusters")
    ax.legend(fontsize=7, loc="upper left")
    ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
    ax.grid(axis="y", alpha=0.3)

    # Panel F: Multi-status Jaccard trend (mean across years)
    ax = axes[1, 2]
    for st in status_list:
        st_jac = [comp_df[(comp_df["status"] == st) & (comp_df["year"] == y)]["jaccard_hh"].values[0]
                  if len(comp_df[(comp_df["status"] == st) & (comp_df["year"] == y)]) > 0 else 0
                  for y in YEARS]
        ax.plot(YEARS, st_jac, "o-", label=st, lw=1.5, markersize=4)
    ax.set_title("F. Jaccard by Status Over Time", fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("Jaccard (rates vs cases HH)")
    ax.set_ylim(0, 1)
    ax.legend(fontsize=7)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
    ax.grid(alpha=0.3)

    plt.tight_layout()
    out = "reports/figures/fig_rates_vs_cases_hh.pdf"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {out}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    Path("reports/figures").mkdir(parents=True, exist_ok=True)

    clf = build_classification()
    all_clusters, comp_df = run_all_analyses(clf)
    print_summary(all_clusters, comp_df)
    make_figure(all_clusters, comp_df)

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    main()
