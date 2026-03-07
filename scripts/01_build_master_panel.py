import pandas as pd
import numpy as np
from pathlib import Path
import os

def build_master():
    print("🚀 Starting Master Panel Construction...")

    # Paths
    pop_path = Path("data/external/conapo_poblacion_1990_2070.parquet")

    local_csv = Path("data/raw/rnpdno_total.csv")
    output_path = Path("data/processed/master_panel.parquet")

    # 1. LOAD RNPDNO
    # rnpdno_total.csv has 'cvegeo' (e.g., 01001)
    df_rnpdno = pd.read_csv(local_csv, dtype={'cvegeo': str})
    df_rnpdno['date'] = pd.to_datetime(df_rnpdno[['year', 'month']].assign(day=1))
    print(f"✅ Loaded {len(df_rnpdno)} RNPDNO records.")

    # 2. LOAD CONAPO
    df_pop = pd.read_parquet(pop_path)
    
    # Standardize IDs: 
    # CONAPO 'cve_geo' is usually int (1001) or string. Force 5-digit string to match RNPDNO.
    df_pop['cvegeo'] = df_pop['cve_geo'].astype(str).str.zfill(5)
    
    # Filter for study period to speed up interpolation
    df_pop = df_pop[(df_pop['year'] >= 2014) & (df_pop['year'] <= 2026)]
    
    # 3. INTERPOLATION LOGIC
    # Anchor yearly population to July 1st
    df_pop['anchor_date'] = pd.to_datetime(df_pop['year'].astype(str) + '-07-01')
    
    print("📈 Interpolating monthly population denominators using 'pob_total'...")
    # Pivot to create a time series
    df_pivot = df_pop.pivot(index='anchor_date', columns='cvegeo', values='pob_total')
    
    # Resample to Month Start (MS) and interpolate
    df_monthly_pop = df_pivot.resample('MS').interpolate(method='linear').stack().reset_index()
    df_monthly_pop.columns = ['date', 'cvegeo', 'pop_dynamic']

    # 4. FINAL MERGE
    df_master = pd.merge(df_rnpdno, df_monthly_pop, on=['cvegeo', 'date'], how='left')

    # 5. ASSIGN POPULATION BANDS
    def assign_band(p):
        if pd.isna(p): return 'Unknown'
        if p >= 1_000_000: return 'Band 5: Millonarias'
        if p >= 500_000:   return 'Band 4: Metropolitan'
        if p >= 100_000:   return 'Band 3: Mid-Size'
        if p >= 25_000:    return 'Band 2: Small Town'
        return 'Band 1: Rural'

    df_master['pop_band'] = df_master['pop_dynamic'].apply(assign_band)
    
    # Calculate Risk Rate (per 100k)
    # Using 'total' column from your rnpdno_total.csv
    df_master['risk_rate'] = (df_master['total'] / df_master['pop_dynamic']) * 100_000

    # 6. SAVE
    os.makedirs("data/processed", exist_ok=True)
    df_master.to_parquet(output_path)
    print(f"🎉 Success! Master panel saved to {output_path}")
    print(df_master[['cvegeo', 'date', 'total', 'pop_dynamic', 'pop_band']].head())

if __name__ == "__main__":
    build_master()
