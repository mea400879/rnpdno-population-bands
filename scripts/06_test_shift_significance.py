"""Statistical test for centroid drift over time."""

import pandas as pd
import numpy as np
from scipy import stats


def test_shift():
    df = pd.read_csv("data/processed/hotspot_centroids.csv")

    if len(df) < 3:
        print("Insufficient data points for trend test")
        return

    years = df['year'].values
    y_coords = df['centroid_y'].values
    x_coords = df['centroid_x'].values

    # Linear regression: Y coordinate ~ year
    slope_y, intercept_y, r_y, p_y, se_y = stats.linregress(years, y_coords)

    # Linear regression: X coordinate ~ year (east-west drift)
    slope_x, intercept_x, r_x, p_x, se_x = stats.linregress(years, x_coords)

    print("=== CENTROID DRIFT SIGNIFICANCE TEST ===\n")

    print("North-South (Y coordinate):")
    print(f"  Slope: {slope_y:,.1f} m/year ({slope_y/1000:.2f} km/year)")
    print(f"  Direction: {'Southward' if slope_y < 0 else 'Northward'}")
    print(f"  R2: {r_y**2:.4f}")
    print(f"  p-value: {p_y:.6f}")
    print(f"  Significant (a=0.05): {'Yes' if p_y < 0.05 else 'No'}")

    print("\nEast-West (X coordinate):")
    print(f"  Slope: {slope_x:,.1f} m/year ({slope_x/1000:.2f} km/year)")
    print(f"  Direction: {'Eastward' if slope_x > 0 else 'Westward'}")
    print(f"  R2: {r_x**2:.4f}")
    print(f"  p-value: {p_x:.6f}")
    print(f"  Significant (a=0.05): {'Yes' if p_x < 0.05 else 'No'}")

    # Total displacement
    total_y = slope_y * (years[-1] - years[0])
    total_x = slope_x * (years[-1] - years[0])
    total_dist = np.sqrt(total_y**2 + total_x**2)

    print(f"\nTotal displacement ({years[0]}-{years[-1]}):")
    print(f"  N-S: {total_y/1000:,.1f} km")
    print(f"  E-W: {total_x/1000:,.1f} km")
    print(f"  Euclidean: {total_dist/1000:,.1f} km")

    # Mann-Kendall trend test (non-parametric alternative)
    try:
        from scipy.stats import kendalltau
        tau_y, p_mk_y = kendalltau(years, y_coords)
        print(f"\nMann-Kendall (Y): t={tau_y:.4f}, p={p_mk_y:.6f}")
    except Exception:
        pass

    # Save results
    results = {
        'test': ['Linear regression (Y)', 'Linear regression (X)', 'Total displacement'],
        'slope_km_year': [slope_y/1000, slope_x/1000, None],
        'r_squared': [r_y**2, r_x**2, None],
        'p_value': [p_y, p_x, None],
        'total_km': [total_y/1000, total_x/1000, total_dist/1000],
    }
    pd.DataFrame(results).to_csv("data/processed/shift_significance.csv", index=False)
    print("\nSaved: data/processed/shift_significance.csv")


if __name__ == "__main__":
    test_shift()
