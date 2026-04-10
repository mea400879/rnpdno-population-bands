# Task 3 -- Bajio Corridor Trend Recomputation

**Date:** 2026-04-09

**Corridor:** 29 municipalities (Medina-Fernandez et al. 2023, SUN 2018)

**Method:** OLS with Newey-West HAC (bandwidth=12)


## 3a-b. Linear Trend Results

| Status | Slope (HH/month) | Slope (HH/year) | SE | p-value | 95% CI |
|--------|-------------------|-----------------|-----|---------|--------|
| Total | -0.0256 | -0.31 | 0.0350 | 0.4649 | [-1.13, 0.52] |
| Not Located | 0.0418 | 0.50 | 0.0123 | 0.0007 | [0.21, 0.79] |
| Located Alive | -0.0289 | -0.35 | 0.0364 | 0.4279 | [-1.20, 0.51] |
| Located Dead | 0.0117 | 0.14 | 0.0095 | 0.2168 | [-0.08, 0.36] |

## 3c. Breakpoint Analysis (Total status)

**Best breakpoint (min-RSS):** 2017-02 (index 25)

**Chow test:** F=78.13, p=0.000000


Structural break confirmed at 2017-02 (p < 0.05).


### Piecewise OLS (Newey-West HAC, bw=12)

| Segment | Period | Slope (HH/year) | p-value | 95% CI |
|---------|--------|-----------------|---------|--------|
| Pre-break | 2014-07 to 2017-02 | -8.82 | 0.0000 | [-10.09, -7.54] |
| Post-break | 2017-02 to 2025-06 | 0.47 | 0.0464 | [0.01, 0.94] |

## 3d. Comparison: Old Bajio (~200 CESOP) vs New Bajio (29 corridor)

| Metric | Old Bajio (~200 CESOP) | New Bajio (29 corridor) |
|--------|----------------------|------------------------|
| Total slope | -1.09/yr (p=0.024) | -0.31/yr (p=0.4649) |
| Not Located slope | from Table 6 | 0.50/yr (p=0.0007) |
| Located Alive slope | from Table 6 | -0.35/yr (p=0.4279) |
| Located Dead slope | from Table 6 | 0.14/yr (p=0.2168) |
| Breakpoint | none tested | 2017-02 (F=78.13, p=0.000000) |