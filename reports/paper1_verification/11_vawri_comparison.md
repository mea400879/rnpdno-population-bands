# 11 — VAWRI Comparison

## Dataset

- **Source:** VAWRI Mexico 2023 (Violence Against Women Risk Index)
- **Municipalities:** 2455 (vs 2478 in LISA)
- **VAWRI range:** 0.000–0.978
- **VAWRI mean:** 0.274, median: 0.208
- **Join key:** CVE_INEGI (5-digit INEGI code) → cvegeo

## VAWRI in HH vs Non-HH Municipalities (Jun 2025)

| Sex | Status | N HH | Mean VAWRI HH | Mean VAWRI non-HH | Median HH | Median non-HH | Mann-Whitney p | Spearman ρ | Spearman p |
|-----|--------|------|---------------|-------------------|-----------|---------------|---------------|-----------|-----------|
| female | Not Located | 50 | 0.784 | 0.263 | 0.866 | 0.200 | 0.0000* | -0.2121 | 0.0000* |
| female | Located Alive | 90 | 0.786 | 0.254 | 0.850 | 0.196 | 0.0000* | -0.2092 | 0.0000* |
| male | Not Located | 85 | 0.741 | 0.257 | 0.810 | 0.196 | 0.0000* | -0.1794 | 0.0000* |
| male | Located Alive | 83 | 0.793 | 0.256 | 0.850 | 0.196 | 0.0000* | -0.1851 | 0.0000* |

## Interpretation

- **Female NL:** HH municipalities have significantly higher VAWRI scores (mean 0.784 vs 0.263, p<0.001). HH municipalities are 3x the national VAWRI average.
- **Female LA:** HH municipalities have significantly higher VAWRI scores (mean 0.786 vs 0.254, p<0.001).
- **Male NL (control):** Male HH municipalities also have significantly higher VAWRI (0.741 vs 0.257, p<0.001). This indicates VAWRI captures general violence exposure in high-disappearance municipalities, not a female-specific spatial signal.
- **Spearman ρ is negative** because local_i is negative for LH municipalities (low counts surrounded by high neighbors) which can also have high VAWRI. The group comparison (Mann-Whitney) is the appropriate test for the HH/non-HH question.
- **Key finding:** Disappearance hotspots — regardless of sex — coincide with high violence-against-women risk. The VAWRI association is not sex-specific; it reflects that HH municipalities are urban areas with high general and gendered violence.

## Tabasco: Female Located Alive HH Municipalities

Unique municipalities with female LA HH classification (2023–2025): **6**

| cvegeo | Municipality | VAWRI |
|--------|-------------|-------|
| 27012 | Macuspana | 0.654 |
| 27006 | Cunduacán | 0.576 |
| 27016 | Teapa | 0.502 |
| 27013 | Nacajuca | 0.482 |
| 27003 | Centla | 0.372 |
| 27009 | Jalapa | 0.274 |

Tabasco state mean VAWRI: 0.462 (national mean: 0.274)
