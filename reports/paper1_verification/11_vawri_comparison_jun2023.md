# 11 — VAWRI External Validation (June 2023 LISA Cross-Section)

## Dataset

- **VAWRI source:** VAWRI Mexico 2023 (Violence Against Women Risk Index)
- **VAWRI municipalities:** 2455
- **VAWRI range:** 0.000–0.978
- **VAWRI mean:** 0.274, median: 0.208
- **LISA cross-section:** 2023-06 (temporally matched to VAWRI 2023)
- **LISA municipalities:** 2478
- **Successfully joined:** 2455 municipalities
- **Join key:** CVE_INEGI (zero-padded to 5 digits) → cvegeo

## Mann-Whitney U Tests: Total Sex, All Statuses

| Status | N HH | N non-HH | Median HH | IQR HH | Median non-HH | IQR non-HH | U | p-value | r_rb |
|--------|------|----------|-----------|--------|---------------|------------|---|---------|------|
| Total | 91 | 2364 | 0.842 | 0.683–0.908 | 0.196 | 0.064–0.382 | 200048 | 1.62e-44* | 0.860 |
| Not Located | 70 | 2385 | 0.850 | 0.571–0.916 | 0.198 | 0.064–0.390 | 151258 | 1.97e-31* | 0.812 |
| Located Alive | 94 | 2361 | 0.822 | 0.619–0.899 | 0.196 | 0.064–0.382 | 201854 | 8.38e-42* | 0.819 |
| Located Dead | 25 | 2430 | 0.872 | 0.802–0.936 | 0.206 | 0.066–0.400 | 57342 | 9.80e-15* | 0.888 |

## Mann-Whitney U Tests: Sex-Disaggregated (Not Located & Located Dead)

| Status | Sex | N HH | N non-HH | Median HH | IQR HH | Median non-HH | IQR non-HH | U | p-value | r_rb |
|--------|-----|------|----------|-----------|--------|---------------|------------|---|---------|------|
| Not Located | male | 78 | 2377 | 0.783 | 0.557–0.911 | 0.198 | 0.064–0.388 | 163067 | 1.47e-30* | 0.759 |
| Not Located | female | 32 | 2423 | 0.890 | 0.857–0.933 | 0.204 | 0.066–0.398 | 75880 | 5.67e-21* | 0.957 |
| Located Dead | male | 22 | 2433 | 0.887 | 0.742–0.938 | 0.206 | 0.066–0.400 | 50870 | 1.57e-13* | 0.901 |
| Located Dead | female | 9 | 2446 | 0.914 | 0.850–0.938 | 0.207 | 0.066–0.408 | 21127 | 9.17e-07* | 0.919 |

## Effect Size Interpretation

The rank-biserial correlation (r_rb) is computed as r = 2U₁/(n₁·n₂) − 1, where U₁ is the Mann-Whitney U for the HH group.
Interpretation (following Kerby 2014): |r| < 0.3 small, 0.3–0.5 medium, > 0.5 large.

## Notes

- **Temporal alignment:** Both VAWRI composite scores and LISA HH classification reference 2023,
  eliminating the 2-year mismatch in the prior analysis (which used June 2025 LISA).
- **Test directionality:** One-sided (greater), testing whether HH municipalities have higher VAWRI.
- **LISA parameters:** Queen contiguity, 999 permutations, α = 0.05.
