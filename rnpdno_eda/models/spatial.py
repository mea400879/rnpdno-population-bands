"""Spatial weights and LISA utilities."""

import geopandas as gpd
import numpy as np
import pandas as pd
from libpysal.weights import Queen, fuzzy_contiguity
from esda.moran import Moran, Moran_Local
from pathlib import Path
import warnings


def load_municipios():
    """Load municipality geometries, ensure EPSG:6372."""
    gdf = gpd.read_parquet("data/external/municipios_2024.geoparquet")

    if gdf.crs is None or gdf.crs.to_epsg() != 6372:
        gdf = gdf.to_crs(epsg=6372)

    # Find cvegeo column (case-insensitive)
    cvegeo_col = None
    for col in gdf.columns:
        if 'cvegeo' in col.lower() or 'cve_geo' in col.lower():
            cvegeo_col = col
            break

    if cvegeo_col is None:
        raise ValueError(f"No cvegeo column found. Columns: {gdf.columns.tolist()}")

    gdf['cvegeo'] = gdf[cvegeo_col].astype(str).str.zfill(5)
    gdf = gdf.set_index('cvegeo')

    return gdf


def build_queen_weights(gdf, buffer=50):
    """Build Queen contiguity weights with fuzzy tolerance.

    Uses fuzzy_contiguity with a small buffer to close sub-metre gaps
    caused by geometry precision issues in the source geoparquet,
    which otherwise produce dozens of false island municipalities.

    Parameters
    ----------
    gdf : GeoDataFrame
        Must be in a projected CRS (e.g. EPSG:6372, metres).
    buffer : float
        Buffer distance in CRS units (metres for EPSG:6372).
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        w = fuzzy_contiguity(gdf, buffering=True, buffer=buffer)
    w.transform = "R"
    return w


def run_lisa(values, w, permutations=999, alpha=0.05):
    """
    Run Local Moran's I.

    Returns dict with:
        - moran_I: global Moran's I
        - p_value: global p-value
        - lisa_I: local I values
        - lisa_p: local p-values
        - clusters: cluster classification (0=NS, 1=HH, 2=LL, 3=LH, 4=HL)
        - n_hh: count of High-High clusters
    """
    # Global
    moran = Moran(values, w, permutations=permutations)

    # Local
    lisa = Moran_Local(values, w, permutations=permutations)

    # Classify
    sig = lisa.p_sim < alpha
    clusters = np.zeros(len(values), dtype=int)
    clusters[sig & (lisa.q == 1)] = 1  # HH
    clusters[sig & (lisa.q == 3)] = 2  # LL
    clusters[sig & (lisa.q == 2)] = 3  # LH
    clusters[sig & (lisa.q == 4)] = 4  # HL

    return {
        'moran_I': moran.I,
        'p_value': moran.p_sim,
        'lisa_I': lisa.Is,
        'lisa_p': lisa.p_sim,
        'clusters': clusters,
        'n_hh': (clusters == 1).sum(),
        'n_ll': (clusters == 2).sum(),
    }
