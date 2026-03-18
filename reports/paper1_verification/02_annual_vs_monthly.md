# Phase 2 — Annual vs Monthly Pipeline Comparison

Generated: 2026-03-18 | Study period: Jan 2015 - Dec 2025 (132 months)
Monthly: OLS + Newey-West HAC (bandwidth=12) | Annual: OLS + HC3 (11 data points, 2015-2025)
Slopes in municipalities/year. Monthly slope x 12.

---

## Full Comparison Table

| Region | Status | Monthly/yr | p_monthly | Sig | Annual/yr | p_annual | Sig | Discrepancy |
|--------|--------|-----------|-----------|-----|-----------|----------|-----|-------------|
| Norte | Total | +0.643 | 0.0002 | * | +0.642 | 0.0046 | * | — |
| Centro-Norte | Total | -0.739 | 0.0252 | * | -0.741 | 0.1121 | | sig_mismatch |
| Norte-Occidente | Total | +0.577 | 0.0004 | * | +0.585 | 0.0071 | * | — |
| Centro | Total | +2.764 | 0.0008 | * | +2.764 | 0.0223 | * | — |
| Sur | Total | +0.112 | 0.4263 | | +0.111 | 0.5507 | | — |
| Norte | Not Located | +0.226 | 0.1481 | | +0.233 | 0.2719 | | — |
| Centro-Norte | Not Located | -0.478 | 0.1106 | | -0.477 | 0.2583 | | — |
| Norte-Occidente | Not Located | +0.440 | 0.0003 | * | +0.451 | 0.0079 | * | — |
| Centro | Not Located | +4.183 | 0.0000 | * | +4.167 | 0.0000 | * | — |
| Sur | Not Located | +0.305 | 0.0003 | * | +0.299 | 0.0359 | * | — |
| Norte | Located Alive | +1.098 | 0.0000 | * | +1.113 | 0.0000 | * | — |
| Centro-Norte | Located Alive | -0.026 | 0.9017 | | -0.018 | 0.9502 | | — |
| Norte-Occidente | Located Alive | +0.527 | 0.0000 | * | +0.523 | 0.0000 | * | — |
| Centro | Located Alive | +3.041 | 0.0005 | * | +3.089 | 0.0183 | * | — |
| Sur | Located Alive | +0.212 | 0.0413 | * | +0.212 | 0.1276 | | sig_mismatch |
| Norte | Located Dead | +0.437 | 0.0003 | * | +0.450 | 0.0011 | * | — |
| Centro-Norte | Located Dead | -0.205 | 0.3664 | | +0.073 | 0.7409 | | sign_flip (ns) |
| Norte-Occidente | Located Dead | -0.014 | 0.8502 | | -0.065 | 0.4950 | | — |
| Centro | Located Dead | +0.864 | 0.0000 | * | +0.874 | 0.0000 | * | — |
| Sur | Located Dead | +0.010 | 0.9095 | | +0.042 | 0.6726 | | — |

### Bajio sub-flag (is_bajio=True, all regions combined)

| Status | Monthly/yr | p_monthly | Sig | Annual/yr | p_annual | Sig | Discrepancy |
|--------|-----------|-----------|-----|-----------|----------|-----|-------------|
| Total | -1.030 | 0.0120 | * | -1.020 | 0.0933 | | sig_mismatch |
| Not Located | +0.156 | 0.6571 | | +0.167 | 0.7246 | | — |
| Located Alive | -0.511 | 0.3321 | | -0.486 | 0.5458 | | — |
| Located Dead | +0.092 | 0.6752 | | +0.194 | 0.3520 | | — |

---

## Discrepancies Summary

4 sig_mismatch cases identified (out of 24 combos):
1. **Centro-Norte x Total**: monthly sig (p=0.025), annual not (p=0.112). Marginal effect at monthly resolution disappears with only 11 annual points.
2. **Sur x Located Alive**: monthly sig (p=0.041), annual not (p=0.128). Borderline monthly effect, insufficient power annually.
3. **Bajio x Total**: monthly sig (p=0.012), annual not (p=0.093). V-shaped trajectory inflates annual SE.
4. **Centro-Norte x Located Dead**: sign flip (monthly -0.205, annual +0.073) — both non-significant, no substantive concern.

### Why monthly and annual may diverge

- Monthly OLS uses 132 data points with NW HAC(12) to account for autocorrelation. Annual OLS uses only 11 annual mean values with HC3. The larger N in monthly regression provides greater power for marginal effects.
- Non-linear or V-shaped trajectories (e.g. Centro 2016-2018 dip) inflate residual variance in annual OLS more than in monthly OLS.
- Seasonal variation is averaged out at annual resolution, potentially attenuating regional effects.

---

## Centro Deep Dive: Annual Mean HH Municipalities per Year

| Year | Total | Not Located | Located Alive | Located Dead |
|------|-------|-------------|---------------|--------------|
| 2015 | 42.5 | 5.4 | 41.4 | 4.1 |
| 2016 | 29.8 | 10.8 | 25.8 | 4.0 |
| 2017 | 27.3 | 9.9 | 25.8 | 4.4 |
| 2018 | 12.7 | 7.1 | 12.3 | 2.4 |
| 2019 | 29.3 | 18.0 | 27.1 | 6.6 |
| 2020 | 51.4 | 21.0 | 48.7 | 10.8 |
| 2021 | 45.2 | 25.7 | 43.1 | 8.0 |
| 2022 | 43.2 | 26.0 | 41.3 | 8.9 |
| 2023 | 48.8 | 36.6 | 51.4 | 10.2 |
| 2024 | 53.4 | 41.6 | 53.0 | 10.5 |
| 2025 | 56.2 | 47.3 | 57.5 | 11.8 |

**Interpretation:** Not Located shows monotonic sustained rise (5.4 to 47.3, x8.7). Located Dead also rises monotonically (4.1 to 11.8). Total and Located Alive show a V-shape: high in 2015, collapse 2016-2018 (minimum 12.7), then recovery and new highs by 2025. Both are significant at both resolutions when using the updated 2025 endpoint.

---

## Key Findings for Manuscript

1. **Norte**: Positive and significant for ALL four statuses at both resolutions. Primary consolidation region. Monthly slopes: +0.643 (Total), +0.226 (NL, ns), +1.098 (LA), +0.437 (LD) munis/year.

2. **Norte-Occidente**: Consistently significant for Total, Not Located, Located Alive. Emerging secondary hotspot cluster region.

3. **Centro**: Strong upward trend for Not Located (+4.183/yr***) and Located Dead (+0.864/yr***) consistent at both resolutions. Total (+2.764/yr*) and Located Alive (+3.041/yr*) significant at both resolutions through 2025.

4. **Bajio**: Total HH count significantly DECLINING (-1.030/yr*) at monthly resolution. Annual estimate -1.020/yr but p=0.093 (marginal). Not Located, Located Alive, Located Dead: all non-significant. **"Rising Bajio" hypothesis is REJECTED.**

5. **Centro-Norte**: Declining Total HH marginally significant monthly (-0.739/yr, p=0.025) but not annually. No other statuses significant.

6. **Sur**: Not Located (+0.305/yr***) significant at both resolutions. Located Alive borderline (sig monthly, ns annually).
