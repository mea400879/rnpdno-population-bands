"""
Bajío-Region spatial cluster analysis.

Steps:
1. Build municipality reference: all 2478 munis get region + is_bajio
2. For each year 2015-2024: find HH munis, build queen-contiguity subgraph,
   find connected components (>=3 munis), classify by dominant region + Bajío
3. Aggregate trends
4. Plot figure

Outputs:
  data/processed/bajio_cvegeo_list.csv
  data/processed/municipality_classification.csv
  data/processed/hh_clusters_by_year.csv
  data/processed/cluster_region_trend.csv
  reports/figures/fig_cluster_trend_by_region.pdf
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
from rnpdno_eda.models.spatial import load_municipios, build_queen_weights

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REGION_MAP = {
    "Norte": [2, 5, 8, 19, 26, 28],
    "Norte-Occidente": [3, 10, 18, 25, 32],
    "Centro-Norte": [1, 6, 14, 16, 24],
    "Centro": [9, 11, 13, 15, 17, 21, 22, 29],
    "Sur": [4, 7, 12, 20, 23, 27, 30, 31],
}

# Build reverse lookup: int cve_ent -> region name
CVE_TO_REGION = {}
for region, cves in REGION_MAP.items():
    for c in cves:
        CVE_TO_REGION[c] = region

# Bajío municipalities by cve_ent (int).
# None = ALL municipalities in that state are Bajío.
# List of str = only those municipalities (accented names OK).
BAJIO_MUNIS = {
    1: None,  # ALL Aguascalientes
    11: None,  # ALL Guanajuato
    22: None,  # ALL Querétaro
    14: [  # Jalisco (54 listed)
        "Acatic", "Arandas", "Cañadas de Obregón", "Encarnación de Díaz",
        "Jalostotitlán", "Jesús María", "Lagos de Moreno", "Mexticacán",
        "Ojuelos de Jalisco", "San Diego de Alejandría", "San Juan de los Lagos",
        "San Julián", "San Miguel el Alto", "Teocaltiche", "Tepatitlán de Morelos",
        "Unión de San Antonio", "Valle de Guadalupe", "Villa Hidalgo",
        "Atotonilco el Alto", "Ayotlán", "Degollado", "Jamay", "La Barca",
        "Ocotlán", "Poncitlán", "Tototlán", "Zapotlán del Rey",
        "Amatitán", "El Arenal", "Magdalena", "San Juanito de Escobedo",
        "Tequila", "Teuchitlán",
        "Guadalajara", "Zapopan", "Tlaquepaque", "Tonalá",
        "Tlajomulco de Zúñiga", "El Salto", "Juanacatlán",
        "Ixtlahuacán de los Membrillos",
        "Ameca", "Cocula", "Etzatlán", "Hostotipaquillo", "San Marcos",
        "Tala", "Ahualulco de Mercado", "Zapotlanejo", "Cuquío",
    ],
    16: [  # Michoacán (34)
        "Álvaro Obregón", "Angamacutiro", "Angangueo", "Churintzio", "Cuitzeo",
        "Ecuandureo", "Huaniqueo", "Indaparapeo", "Irimbo", "Jiménez",
        "José Sixto Verduzco", "Lagunillas", "La Piedad", "Maravatío", "Morelia",
        "Morelos", "Panindícuaro", "Penjamillo", "Purépero", "Puruándiro",
        "Queréndaro", "Santa Ana Maya", "Senguio", "Tangancícuaro", "Tanhuato",
        "Tarímbaro", "Tlalpujahua", "Tlazazalca", "Tuxpan", "Villa Jiménez",
        "Villa Morelos", "Yurécuaro", "Zináparo", "Zacapu",
    ],
    24: [  # San Luis Potosí (15)
        "Ahualulco", "Armadillo de los Infante", "Cerro de San Pedro",
        "Guadalcázar", "Mexquitic de Carmona", "Moctezuma", "San Luis Potosí",
        "Santa María del Río", "Soledad de Graciano Sánchez", "Villa de Arriaga",
        "Villa de Reyes", "Villa Hidalgo", "Villa de Zaragoza", "Villa Juárez",
        "Escalerillas",
    ],
    32: [  # Zacatecas (31)
        "Apozol", "Apulco", "Atolinga", "Benito Juárez", "Calera",
        "Cañitas de Felipe Pescador", "Chalchihuites", "Cuauhtémoc",
        "El Plateado de Joaquín Amaro", "Florencia de Benito Juárez",
        "Fresnillo", "Genaro Codina", "General Enrique Estrada",
        "General Pánfilo Natera", "Guadalupe", "Huanusco", "Jalpa", "Jerez",
        "Juchipila", "Luis Moya", "Momax", "Nochistlán", "Noria de Ángeles",
        "Ojocaliente", "Pánfilo Natera", "Tabasco", "Tepechitlán",
        "Teúl de González Ortega", "Tlaltenango", "Trancoso", "Zacatecas",
    ],
}

MIN_CLUSTER_SIZE = 3


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def strip_accents(s: str) -> str:
    """Remove diacritics and lowercase for fuzzy matching."""
    nfkd = unicodedata.normalize("NFKD", str(s))
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn").lower().strip()


def connected_components(nodes: set, adjacency: dict) -> list[list]:
    """BFS connected components restricted to `nodes`."""
    visited = set()
    components = []
    for start in nodes:
        if start in visited:
            continue
        component = []
        queue = [start]
        visited.add(start)
        while queue:
            curr = queue.pop(0)
            component.append(curr)
            for nbr in adjacency.get(curr, []):
                if nbr in nodes and nbr not in visited:
                    visited.add(nbr)
                    queue.append(nbr)
        components.append(component)
    return components


# ---------------------------------------------------------------------------
# STEP 1: Build municipality reference table
# ---------------------------------------------------------------------------

def build_municipality_reference():
    print("=" * 60)
    print("STEP 1: Building municipality reference table")
    print("=" * 60)

    # Load AGEEML
    ageeml = pd.read_csv("data/external/ageeml_catalog.csv", encoding="latin-1")
    ageeml["cvegeo"] = ageeml["CVEGEO"].astype(str).str.zfill(5)
    ageeml["cve_ent_int"] = ageeml["CVE_ENT"].astype(int)
    ageeml["nom_mun_norm"] = ageeml["NOM_MUN"].apply(strip_accents)

    # Assign region
    ageeml["region"] = ageeml["cve_ent_int"].map(CVE_TO_REGION)
    missing_region = ageeml["region"].isna().sum()
    if missing_region:
        print(f"WARNING: {missing_region} municipalities with no region assignment")

    # --- Match Bajío ---
    ageeml["is_bajio"] = False
    bajio_cvegeos = []
    unmatched = []

    # States where ALL municipalities are Bajío
    all_bajio_states = [cve for cve, lst in BAJIO_MUNIS.items() if lst is None]
    mask_all = ageeml["cve_ent_int"].isin(all_bajio_states)
    ageeml.loc[mask_all, "is_bajio"] = True
    n_all = mask_all.sum()
    print(f"  ALL-state Bajío municipalities matched: {n_all} (states {all_bajio_states})")

    # States with partial Bajío lists
    partial_states = {cve: lst for cve, lst in BAJIO_MUNIS.items() if lst is not None}
    n_matched_partial = 0

    for cve_ent, names in partial_states.items():
        subset = ageeml[ageeml["cve_ent_int"] == cve_ent].copy()
        norm_to_cvegeo = dict(zip(subset["nom_mun_norm"], subset["cvegeo"]))

        for name in names:
            norm = strip_accents(name)
            if norm in norm_to_cvegeo:
                cvegeo = norm_to_cvegeo[norm]
                ageeml.loc[ageeml["cvegeo"] == cvegeo, "is_bajio"] = True
                n_matched_partial += 1
            else:
                unmatched.append((cve_ent, name))

    print(f"  Partial-state Bajío municipalities matched: {n_matched_partial}")
    total_bajio = ageeml["is_bajio"].sum()
    total_listed = sum(
        len(v) if v is not None else ageeml[ageeml["cve_ent_int"] == k].shape[0]
        for k, v in BAJIO_MUNIS.items()
    )
    print(f"\n  BAJÍO MATCH RATE: {total_bajio}/{total_listed} "
          f"({100 * total_bajio / total_listed:.1f}%)")

    if unmatched:
        print(f"\n  UNMATCHED Bajío names ({len(unmatched)}):")
        for cve, name in unmatched:
            print(f"    CVE_ENT={cve:02d}: '{name}'")
            # Try to show closest AGEEML names
            subset_names = ageeml[ageeml["cve_ent_int"] == cve]["NOM_MUN"].tolist()
            norm_target = strip_accents(name)
            close = [n for n in subset_names if strip_accents(n)[:4] == norm_target[:4]]
            if close:
                print(f"      (similar in AGEEML: {close[:3]})")
    else:
        print("  All Bajío municipalities matched successfully.")

    # Save bajio list
    bajio_df = ageeml[ageeml["is_bajio"]][["cvegeo", "NOM_MUN", "CVE_ENT"]].copy()
    bajio_df.columns = ["cvegeo", "nom_mun", "cve_estado"]
    bajio_df = bajio_df.sort_values("cvegeo").reset_index(drop=True)
    bajio_df.to_csv("data/processed/bajio_cvegeo_list.csv", index=False)
    print(f"\n  Saved: data/processed/bajio_cvegeo_list.csv ({len(bajio_df)} rows)")

    # Save full classification
    class_df = ageeml[["cvegeo", "region", "is_bajio"]].sort_values("cvegeo").reset_index(drop=True)
    class_df.to_csv("data/processed/municipality_classification.csv", index=False)
    print(f"  Saved: data/processed/municipality_classification.csv ({len(class_df)} rows)")

    return class_df


# ---------------------------------------------------------------------------
# STEP 2: Annual HH connected components
# ---------------------------------------------------------------------------

def build_annual_clusters(class_df: pd.DataFrame):
    print("\n" + "=" * 60)
    print("STEP 2: Annual HH spatial clusters (connected components)")
    print("=" * 60)

    # Load spatial data and build weights once
    gdf = load_municipios()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        w = build_queen_weights(gdf)

    adjacency = w.neighbors  # dict: cvegeo -> [neighbors]
    print(f"  Municipalities: {len(gdf)}, Queen pairs: {sum(len(v) for v in adjacency.values()) // 2}")

    # Load geoparquet for centroids
    geo_raw = gpd.read_parquet("data/external/municipios_2024.geoparquet")
    geo_raw["cvegeo"] = geo_raw["cve_geo"].astype(str).str.zfill(5)
    centroids = geo_raw.set_index("cvegeo")[["centroid_lon", "centroid_lat"]]

    # Load LISA results
    lisa = pd.read_parquet("data/processed/lisa_annual_clusters.parquet")
    lisa["cvegeo"] = lisa["cvegeo"].astype(str).str.zfill(5)

    # Municipality classification lookup
    clf = class_df.set_index("cvegeo")

    cluster_rows = []

    for year in range(2015, 2025):
        year_lisa = lisa[lisa["year"] == year]
        hh_set = set(year_lisa[year_lisa["cluster"] == 1]["cvegeo"].tolist())
        n_hh_total = len(hh_set)

        # Connected components (restricted to HH municipalities)
        components = connected_components(hh_set, adjacency)

        # Filter by minimum size
        valid = [c for c in components if len(c) >= MIN_CLUSTER_SIZE]
        dropped = len(components) - len(valid)

        year_clusters = 0
        for comp_idx, comp in enumerate(valid):
            comp_set = set(comp)

            # Region: mode of member municipalities
            regions = [clf.loc[cv, "region"] for cv in comp if cv in clf.index]
            if not regions:
                dom_region = "Unknown"
            else:
                dom_region = Counter(regions).most_common(1)[0][0]

            # Bajío: majority of members
            bajio_flags = [clf.loc[cv, "is_bajio"] for cv in comp if cv in clf.index]
            pct_bajio = sum(bajio_flags) / len(bajio_flags) if bajio_flags else 0.0
            is_bajio_cluster = pct_bajio >= 0.5

            # Centroid: mean of member centroids
            lons = [centroids.loc[cv, "centroid_lon"] for cv in comp if cv in centroids.index]
            lats = [centroids.loc[cv, "centroid_lat"] for cv in comp if cv in centroids.index]
            cx = float(np.mean(lons)) if lons else np.nan
            cy = float(np.mean(lats)) if lats else np.nan

            cluster_rows.append({
                "year": year,
                "cluster_id": f"{year}_{comp_idx + 1:03d}",
                "n_munis": len(comp),
                "region": dom_region,
                "pct_bajio": round(pct_bajio, 4),
                "is_bajio_cluster": is_bajio_cluster,
                "centroid_x": round(cx, 6),
                "centroid_y": round(cy, 6),
            })
            year_clusters += 1

        print(
            f"  {year}: {n_hh_total} HH munis → "
            f"{len(components)} raw components → "
            f"{year_clusters} valid (≥{MIN_CLUSTER_SIZE}), "
            f"dropped {dropped} small"
        )

    clusters_df = pd.DataFrame(cluster_rows)
    clusters_df.to_csv("data/processed/hh_clusters_by_year.csv", index=False)
    print(f"\n  Saved: data/processed/hh_clusters_by_year.csv ({len(clusters_df)} rows)")
    return clusters_df


# ---------------------------------------------------------------------------
# STEP 3: Aggregate trends
# ---------------------------------------------------------------------------

def aggregate_trends(clusters_df: pd.DataFrame):
    print("\n" + "=" * 60)
    print("STEP 3: Aggregate cluster trends by region")
    print("=" * 60)

    # Count clusters and HH munis per year per region
    trend = (
        clusters_df
        .groupby(["year", "region"])
        .agg(n_clusters=("cluster_id", "count"), n_hh_munis=("n_munis", "sum"))
        .reset_index()
    )
    trend.to_csv("data/processed/cluster_region_trend.csv", index=False)
    print(f"  Saved: data/processed/cluster_region_trend.csv ({len(trend)} rows)")

    # Print Norte vs Bajío summary
    print("\n  Norte clusters:")
    norte = trend[trend["region"] == "Norte"][["year", "n_clusters", "n_hh_munis"]]
    print(norte.to_string(index=False))

    print("\n  Bajío clusters (by cluster is_bajio flag):")
    bajio_trend = (
        clusters_df[clusters_df["is_bajio_cluster"]]
        .groupby("year")
        .agg(n_clusters=("cluster_id", "count"), n_hh_munis=("n_munis", "sum"))
        .reset_index()
    )
    print(bajio_trend.to_string(index=False))

    # Print 2015 vs 2024 comparison
    print("\n  --- Norte vs Bajío: 2015 vs 2024 ---")
    for yr in [2015, 2024]:
        norte_c = clusters_df[(clusters_df["year"] == yr) & (clusters_df["region"] == "Norte")]
        bajio_c = clusters_df[(clusters_df["year"] == yr) & clusters_df["is_bajio_cluster"]]
        print(
            f"  {yr}: Norte={len(norte_c)} clusters ({norte_c['n_munis'].sum()} munis) | "
            f"Bajío={len(bajio_c)} clusters ({bajio_c['n_munis'].sum()} munis)"
        )

    return trend, bajio_trend


# ---------------------------------------------------------------------------
# STEP 4: Statistical test for Norte→Bajío shift
# ---------------------------------------------------------------------------

def test_shift(clusters_df: pd.DataFrame):
    print("\n" + "=" * 60)
    print("STEP 4: Statistical test — Norte shrinking, Bajío emerging")
    print("=" * 60)

    from scipy import stats

    years = list(range(2015, 2025))

    # Annual Norte HH muni counts
    norte_hh = []
    bajio_hh = []
    for yr in years:
        nc = clusters_df[(clusters_df["year"] == yr) & (clusters_df["region"] == "Norte")]["n_munis"].sum()
        bc = clusters_df[(clusters_df["year"] == yr) & clusters_df["is_bajio_cluster"]]["n_munis"].sum()
        norte_hh.append(nc)
        bajio_hh.append(bc)

    # Spearman rank correlation with time
    slope_n, intercept_n, r_n, p_n, _ = stats.linregress(years, norte_hh)
    slope_b, intercept_b, r_b, p_b, _ = stats.linregress(years, bajio_hh)

    print(f"\n  Norte HH munis in clusters (trend):")
    print(f"    Slope={slope_n:.2f}/yr, R²={r_n**2:.3f}, p={p_n:.4f}")
    print(f"  Bajío HH munis in clusters (trend):")
    print(f"    Slope={slope_b:.2f}/yr, R²={r_b**2:.3f}, p={p_b:.4f}")

    print(f"\n  Interpretation:")
    if p_n < 0.05 and slope_n < 0:
        print(f"    Norte: SIGNIFICANT DECLINE (p={p_n:.3f})")
    elif slope_n < 0:
        print(f"    Norte: declining trend (p={p_n:.3f}, not significant)")
    else:
        print(f"    Norte: no declining trend (p={p_n:.3f})")

    if p_b < 0.05 and slope_b > 0:
        print(f"    Bajío: SIGNIFICANT GROWTH (p={p_b:.3f})")
    elif slope_b > 0:
        print(f"    Bajío: growing trend (p={p_b:.3f}, not significant)")
    else:
        print(f"    Bajío: no growing trend (p={p_b:.3f})")

    return {
        "norte_years": years, "norte_hh": norte_hh,
        "bajio_hh": bajio_hh,
        "norte_slope": slope_n, "norte_p": p_n,
        "bajio_slope": slope_b, "bajio_p": p_b,
    }


# ---------------------------------------------------------------------------
# STEP 5: Figure
# ---------------------------------------------------------------------------

REGION_COLORS = {
    "Norte": "#D62728",
    "Norte-Occidente": "#FF7F0E",
    "Centro-Norte": "#2CA02C",
    "Centro": "#1F77B4",
    "Sur": "#9467BD",
}


def make_figure(clusters_df: pd.DataFrame, trend_df: pd.DataFrame, shift_stats: dict):
    print("\n" + "=" * 60)
    print("STEP 5: Generating figure")
    print("=" * 60)

    years = list(range(2015, 2025))
    regions = list(REGION_MAP.keys())

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        "Spatial Dynamics of High-High Disappearance Clusters\n"
        "Mexico 2015–2024 (Queen contiguity, min. 3 municipalities)",
        fontsize=13, fontweight="bold", y=0.98
    )

    # --- Panel A: Cluster count by region ---
    ax = axes[0, 0]
    pivot_clusters = trend_df.pivot(index="year", columns="region", values="n_clusters").reindex(columns=regions).fillna(0)
    bottom = np.zeros(len(years))
    for region in regions:
        vals = pivot_clusters.get(region, pd.Series(0, index=years)).reindex(years).fillna(0).values
        ax.bar(years, vals, bottom=bottom, color=REGION_COLORS[region], label=region, alpha=0.85)
        bottom += vals
    ax.set_title("A. Number of HH Clusters by Region", fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("Clusters (≥3 municipalities)")
    ax.legend(fontsize=7, loc="upper left")
    ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
    ax.grid(axis="y", alpha=0.3)

    # --- Panel B: HH municipalities by region ---
    ax = axes[0, 1]
    pivot_munis = trend_df.pivot(index="year", columns="region", values="n_hh_munis").reindex(columns=regions).fillna(0)
    bottom = np.zeros(len(years))
    for region in regions:
        vals = pivot_munis.get(region, pd.Series(0, index=years)).reindex(years).fillna(0).values
        ax.bar(years, vals, bottom=bottom, color=REGION_COLORS[region], label=region, alpha=0.85)
        bottom += vals
    ax.set_title("B. HH Municipalities in Clusters by Region", fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("Municipalities in clusters")
    ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
    ax.grid(axis="y", alpha=0.3)

    # --- Panel C: Norte vs Bajío cluster count ---
    ax = axes[1, 0]
    norte_n = []
    bajio_n = []
    for yr in years:
        nc = len(clusters_df[(clusters_df["year"] == yr) & (clusters_df["region"] == "Norte")])
        bc = len(clusters_df[(clusters_df["year"] == yr) & clusters_df["is_bajio_cluster"]])
        norte_n.append(nc)
        bajio_n.append(bc)

    ax.plot(years, norte_n, "o-", color=REGION_COLORS["Norte"], label="Norte clusters", linewidth=2)
    ax.plot(years, bajio_n, "s-", color="#E377C2", label="Bajío clusters", linewidth=2)
    # Linear trend lines
    from numpy.polynomial import polynomial as P
    if len(years) > 1:
        yr_arr = np.array(years)
        for vals, col in [(norte_n, REGION_COLORS["Norte"]), (bajio_n, "#E377C2")]:
            c = np.polyfit(yr_arr, vals, 1)
            ax.plot(yr_arr, np.polyval(c, yr_arr), "--", color=col, alpha=0.5, linewidth=1)

    ax.set_title("C. Norte vs Bajío: Cluster Count Trend", fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of spatial clusters")
    ax.legend(fontsize=9)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
    ax.grid(alpha=0.3)

    # --- Panel D: Norte vs Bajío HH municipality count ---
    ax = axes[1, 1]
    norte_hh = shift_stats["norte_hh"]
    bajio_hh = shift_stats["bajio_hh"]

    ax.plot(years, norte_hh, "o-", color=REGION_COLORS["Norte"], label="Norte (in clusters)", linewidth=2)
    ax.plot(years, bajio_hh, "s-", color="#E377C2", label="Bajío (in clusters)", linewidth=2)

    # Annotate trend stats
    ax.text(
        0.05, 0.95,
        f"Norte: slope={shift_stats['norte_slope']:.1f}/yr, p={shift_stats['norte_p']:.3f}\n"
        f"Bajío: slope={shift_stats['bajio_slope']:.1f}/yr, p={shift_stats['bajio_p']:.3f}",
        transform=ax.transAxes, fontsize=8, va="top",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8)
    )

    ax.set_title("D. Norte vs Bajío: HH Municipalities in Clusters", fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("Municipalities")
    ax.legend(fontsize=9)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
    ax.grid(alpha=0.3)

    plt.tight_layout()
    out_path = "reports/figures/fig_cluster_trend_by_region.pdf"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {out_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Step 1
    class_df = build_municipality_reference()

    # Step 2
    clusters_df = build_annual_clusters(class_df)

    # Step 3
    trend_df, bajio_trend = aggregate_trends(clusters_df)

    # Step 4
    shift_stats = test_shift(clusters_df)

    # Step 5
    make_figure(clusters_df, trend_df, shift_stats)

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    main()
