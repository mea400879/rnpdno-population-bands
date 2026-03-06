import pandas as pd

def analyze():
    df = pd.read_parquet("data/processed/master_panel.parquet")
    
    # 1. Summary by Band
    summary = df.groupby('pop_band').agg({
        'total': 'sum',
        'risk_rate': 'mean',
        'cvegeo': 'nunique'
    }).rename(columns={'cvegeo': 'num_municipalities'})
    
    print("📊 Summary Statistics by Population Band:")
    print(summary)
    
    # 2. The Jaccard Gap (Top 100 for a specific year, e.g., 2023)
    latest = df[df['date'].dt.year == 2023].groupby('cvegeo').agg({
        'total': 'sum',
        'risk_rate': 'mean'
    })
    
    top_burden = set(latest.nlargest(100, 'total').index)
    top_risk = set(latest.nlargest(100, 'risk_rate').index)
    
    intersection = top_burden.intersection(top_risk)
    jaccard = len(intersection) / len(top_burden.union(top_risk))
    
    print(f"\n📉 Jaccard Similarity (Top 100 Burden vs Risk): {jaccard:.2%}")
    print(f"Only {len(intersection)} municipalities appear in both top 100 lists.")

if __name__ == "__main__":
    analyze()
