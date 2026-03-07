"""Compute High-High cluster centroid for each year."""

import pandas as pd
import geopandas as gpd
import numpy as np
from scipy import stats
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from rnpdno_eda.models.spatial import load_municipios


def compute_centroids():
    # Load
    gdf = load_municipios()
    clusters = pd.read_parquet("data/processed/lisa_annual_clusters.parquet")

    centroids = []

    for year in range(2015, 2025):
        # Get HH municipalities for this year
        year_hh = clusters[(clusters['year'] == year) & (clusters['cluster'] == 1)]
        hh_cvegeos = year_hh['cvegeo'].tolist()

        if len(hh_cvegeos) == 0:
            print(f"{year}: No HH clusters")
            continue

        # Get geometries
        hh_gdf = gdf[gdf.index.isin(hh_cvegeos)]

        # Compute centroid of union
        union_geom = hh_gdf.geometry.unary_union
        centroid = union_geom.centroid

        centroids.append({
            'year': year,
            'centroid_x': centroid.x,
            'centroid_y': centroid.y,
            'n_hotspots': len(hh_cvegeos),
        })

        print(f"{year}: {len(hh_cvegeos)} HH clusters, centroid Y={centroid.y:,.0f} m")

    centroids_df = pd.DataFrame(centroids)

    # Compute shift
    if len(centroids_df) >= 2:
        start_y = centroids_df.iloc[0]['centroid_y']
        end_y = centroids_df.iloc[-1]['centroid_y']
        shift_km = (start_y - end_y) / 1000

        print(f"\n=== GEOGRAPHIC SHIFT ===")
        print(f"Start Y ({centroids_df.iloc[0]['year']}): {start_y:,.0f} m")
        print(f"End Y ({centroids_df.iloc[-1]['year']}):   {end_y:,.0f} m")
        print(f"Net shift: {shift_km:,.1f} km {'southward' if shift_km > 0 else 'northward'}")

    # Save
    centroids_df.to_csv("data/processed/hotspot_centroids.csv", index=False)
    print(f"\nSaved: data/processed/hotspot_centroids.csv")

    return centroids_df


if __name__ == "__main__":
    compute_centroids()
