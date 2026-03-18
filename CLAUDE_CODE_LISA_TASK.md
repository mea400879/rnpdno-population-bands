# CLAUDE CODE TASK: Annual LISA + Centroid Trajectory

## Context
- **Project:** `/home/marco/workspace/work/rnpdno-population-bands/`
- **Environment:** `conda activate rnpdno_eda`
- **Input:** `data/processed/master_panel.parquet` (already built)
- **Goal:** Test geographic shift hypothesis (North → Bajío, 2015–2024)

## Constraints
- Raw rates (no EB smoothing for now)
- Annual LISA (10 time points: 2015–2024)
- Exclude Unknown band municipalities
- EPSG:6372 for all spatial operations

---

## TASK 1: Compute Annual Rates

Create `scripts/03_annual_rates.py`:

```python
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
```

---

## TASK 2: Create Spatial Weights

Create `rnpdno_eda/models/spatial.py`:

```python
"""Spatial weights and LISA utilities."""

import geopandas as gpd
import numpy as np
import pandas as pd
from libpysal.weights import Queen
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


def build_queen_weights(gdf):
    """Build Queen contiguity weights."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        w = Queen.from_dataframe(gdf, use_index=True)
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
```

---

## TASK 3: Annual LISA Analysis

Create `scripts/04_annual_lisa.py`:

```python
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
```

---

## TASK 4: Centroid Trajectory

Create `scripts/05_centroid_trajectory.py`:

```python
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
```

---

## TASK 5: Test Significance of Geographic Shift

Create `scripts/06_test_shift_significance.py`:

```python
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
    print(f"  R²: {r_y**2:.4f}")
    print(f"  p-value: {p_y:.6f}")
    print(f"  Significant (α=0.05): {'Yes' if p_y < 0.05 else 'No'}")
    
    print("\nEast-West (X coordinate):")
    print(f"  Slope: {slope_x:,.1f} m/year ({slope_x/1000:.2f} km/year)")
    print(f"  Direction: {'Eastward' if slope_x > 0 else 'Westward'}")
    print(f"  R²: {r_x**2:.4f}")
    print(f"  p-value: {p_x:.6f}")
    print(f"  Significant (α=0.05): {'Yes' if p_x < 0.05 else 'No'}")
    
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
        print(f"\nMann-Kendall (Y): τ={tau_y:.4f}, p={p_mk_y:.6f}")
    except:
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
```

---

## Execution Order

```bash
cd ~/workspace/work/rnpdno-population-bands
conda activate rnpdno_eda

# 1. Compute annual rates
python scripts/03_annual_rates.py

# 2. Run annual LISA (2015-2024)
python scripts/04_annual_lisa.py

# 3. Compute centroid trajectory
python scripts/05_centroid_trajectory.py

# 4. Test significance
python scripts/06_test_shift_significance.py
```

---

## Expected Outputs

| File | Content |
|------|---------|
| `data/processed/annual_rates.parquet` | Municipality-year rates |
| `data/processed/lisa_annual_summary.csv` | Moran's I + HH counts per year |
| `data/processed/lisa_annual_clusters.parquet` | Cluster assignment per muni-year |
| `data/processed/hotspot_centroids.csv` | Annual centroid coordinates |
| `data/processed/shift_significance.csv` | Regression results |

---

## Report Back

After running, report:
1. Global Moran's I trend (increasing/decreasing autocorrelation?)
2. HH cluster count trend
3. Centroid Y slope and p-value
4. Any errors or unexpected results
