"""Run LISA for each year 2015-2024."""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from rnpdno_eda.models.spatial import load_municipios, build_queen_weights, run_lisa


def run_annual_lisa():
    # Load data
    annual = pd.read_parquet("data/processed/annual_rates.parquet")
    gdf = load_municipios()
    w = build_queen_weights(gdf)

    print(f"Geodataframe: {len(gdf)} municipalities")
    print(f"Weights: {w.n} obs, mean neighbors: {w.mean_neighbors:.1f}")

    results = []
    lisa_details = []

    for year in range(2015, 2025):
        # Get year data
        year_data = annual[annual['year'] == year].set_index('cvegeo')

        # Align with weights order
        aligned = year_data.reindex(w.id_order)
        values = aligned['rate'].fillna(0).values

        # Run LISA
        res = run_lisa(values, w, permutations=999, alpha=0.05)

        results.append({
            'year': year,
            'moran_I': res['moran_I'],
            'p_value': res['p_value'],
            'n_hh': res['n_hh'],
            'n_ll': res['n_ll'],
        })

        # Store cluster assignments
        for i, cvegeo in enumerate(w.id_order):
            lisa_details.append({
                'year': year,
                'cvegeo': cvegeo,
                'cluster': res['clusters'][i],
                'lisa_I': res['lisa_I'][i],
                'lisa_p': res['lisa_p'][i],
            })

        sig = "***" if res['p_value'] < 0.001 else "**" if res['p_value'] < 0.01 else "*" if res['p_value'] < 0.05 else ""
        print(f"{year}: I={res['moran_I']:.4f}, p={res['p_value']:.4f}{sig}, HH={res['n_hh']}, LL={res['n_ll']}")

    # Save
    results_df = pd.DataFrame(results)
    results_df.to_csv("data/processed/lisa_annual_summary.csv", index=False)

    details_df = pd.DataFrame(lisa_details)
    details_df.to_parquet("data/processed/lisa_annual_clusters.parquet")

    print(f"\nSaved: data/processed/lisa_annual_summary.csv")
    print(f"Saved: data/processed/lisa_annual_clusters.parquet")

    return results_df, details_df


if __name__ == "__main__":
    run_annual_lisa()
