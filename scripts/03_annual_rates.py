"""Aggregate master panel to annual rates per municipality."""

import pandas as pd
from pathlib import Path

def compute_annual_rates():
    df = pd.read_parquet("data/processed/master_panel.parquet")

    # Exclude Unknown
    df = df[df['pop_band'] != 'Unknown'].copy()

    # Extract year
    df['year'] = df['date'].dt.year

    # Aggregate: sum cases, mean population per year
    annual = df.groupby(['cvegeo', 'year']).agg({
        'total': 'sum',
        'pop_dynamic': 'mean',
        'pop_band': 'first'
    }).reset_index()

    # Compute raw rate (per 100k)
    annual['rate'] = (annual['total'] / annual['pop_dynamic']) * 100_000

    # Handle inf/nan
    annual['rate'] = annual['rate'].replace([float('inf'), float('-inf')], 0).fillna(0)

    # Save
    output = Path("data/processed/annual_rates.parquet")
    annual.to_parquet(output)

    print(f"Saved: {output}")
    print(f"Shape: {annual.shape}")
    print(f"Years: {sorted(annual['year'].unique())}")
    print(f"Municipalities: {annual['cvegeo'].nunique()}")

    # Quick sanity check
    print("\nRate summary by year:")
    print(annual.groupby('year')['rate'].describe()[['mean', 'std', 'max']])

    return annual

if __name__ == "__main__":
    compute_annual_rates()
