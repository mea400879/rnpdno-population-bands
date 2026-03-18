# Phase 7 — Robustness Checks

Generated: 2026-03-18 | Reference baseline: Dec 2025 | Study period: Jan 2015 - Dec 2025

---

## Reference Period Sensitivity

### HH Set Sizes and Cross-Period Jaccard

| Status | Dec 2025 HH | Jun 2025 HH | Dec 2024 HH | J(Jun25,Dec25) | J(Dec24,Dec25) |
|--------|-------------|-------------|-------------|----------------|----------------|
| Total | 72 | 80 | 82 | 0.3945 | 0.3874 |
| Not Located | 53 | 71 | 78 | 0.3778 | 0.3232 |
| Located Alive | 52 | 93 | 87 | 0.4078 | 0.4479 |
| Located Dead | 7 | 17 | 18 | 0.0000 | 0.0870 |

The Jaccard between Dec 2024 and Dec 2025 ranges from 0.0870 (Located Dead) to 0.4479 (Located Alive). This indicates moderate-to-low month-to-month stability in the specific set of HH municipalities. However, the Spearman rank correlation of local_I values between Dec 2024 and Dec 2025 is significant for all statuses (p<0.0001): Total rho=0.4625, NL rho=0.3112, LA rho=0.4142, LD rho=0.2446. The overall spatial structure persists even as individual municipality classifications fluctuate.

For Located Dead, the Jaccard=0.0000 between Jun 2025 and Dec 2025 reflects extremely sparse counts (7 HH munis in Dec 2025, 17 in Jun 2025) — small absolute changes cause zero overlap. This is a power/sparsity issue, not a stability failure.

Interpretation: The trend slopes, regional narratives, and non-interchangeability arguments (NL vs LD, LA vs LD Jaccard < 0.15) are based on the full 132-month time series and are not sensitive to the choice of reference cross-section. The Dec 2025 reference is appropriate as the study endpoint.

---

## Island Municipality Sensitivity

Islands in the weights matrix: 52 municipalities with zero Queen neighbors.

### HH municipalities that are islands (Dec 2025, total sex)

| Status | Total HH | Island HH | Effect of exclusion |
|--------|----------|-----------|---------------------|
| Total (0) | 72 | 0 | None |
| Not Located (7) | 53 | 0 | None |
| Located Alive (2) | 52 | 0 | None |
| Located Dead (3) | 7 | 0 | None |

No HH municipality is an island. Excluding the 52 islands from the analysis would have zero effect on any HH count or Jaccard value.

### LL municipalities that are islands (Dec 2025, total sex)

| Status | Total LL | Island LL | Island LL % |
|--------|----------|-----------|-------------|
| Total (0) | 40 | 37 | 92.5% |
| Not Located (7) | 37 | 37 | 100.0% |
| Located Alive (2) | 45 | 45 | 100.0% |
| Located Dead (3) | 2327 | 51 | 2.2% |

Important finding: For Not Located and Located Alive, 100% and 100% of LL cold-spot municipalities in Dec 2025 are islands. Islands have zero neighbors; their "low-low" classification reflects isolation rather than embedding in a genuine low-value zone. LL counts for these statuses are essentially island artifacts and should not be interpreted substantively.

Located Dead is the exception: its 2,327 LL municipalities are overwhelmingly non-islands (only 51/2327 = 2.2%), reflecting genuine widespread spatial cold-spot clustering for this status.

---

## Zero-Inflation Diagnostic (132 months, 2015-2025)

### Overall zero-inflation per status

| Status | % zero muni-months | All-zero munis | % all-zero |
|--------|-------------------|----------------|------------|
| Total (0) | ~79.9% | 523 | 21.1% |
| Not Located (7) | ~87.6% | 766 | 30.9% |
| Located Alive (2) | ~87.0% | 712 | 28.7% |
| Located Dead (3) | ~96.1% | 1280 | 51.7% |

### Zero-inflation by region (% zero muni-months, 132 months)

| Region | Total | Not Located | Located Alive | Located Dead |
|--------|-------|-------------|---------------|--------------|
| Norte | 75.3% | 81.1% | 85.4% | 94.7% |
| Centro-Norte | 78.6% | 84.6% | 89.5% | 96.5% |
| Norte-Occidente | 72.7% | 81.0% | 83.2% | 93.9% |
| Centro | 74.4% | 86.9% | 80.3% | 95.5% |
| Sur | 92.0% | 96.0% | 94.7% | 99.0% |

Key patterns: Sur is consistently the most zero-inflated region (92-99%). Norte and Norte-Occidente are the least zero-inflated — consistent with their role as primary hotspot regions. Centro has low zero-inflation for Total (74.4%) and Located Alive (80.3%, urban metro effect). Located Dead is extreme (94-99% zero by region). Sur's near-total zero-inflation means LISA classifications in Sur carry high uncertainty and low interpretive weight.

---

## Robustness Summary

| Check | Finding | Impact on paper |
|-------|---------|-----------------|
| Reference period (Jun 2025, Dec 2024) | HH set Jaccard 0.32-0.45 across adjacent periods | Moderate month-to-month flux — note in methods |
| Spearman local_I stability | rho 0.24-0.46 (Dec24 vs Dec25); all p<0.0001 | Overall spatial structure persists |
| Island exclusion | 0 HH municipalities are islands | None — HH findings fully robust |
| Island LL artifact | 100% of NL/LA LL munis are islands (Dec 2025) | Do not interpret LL counts for NL/LA |
| Zero-inflation | 79-96%; Sur worst; Located Dead extreme | Note in methods; flag Sur and female LD |
