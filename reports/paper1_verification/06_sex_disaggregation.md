# Phase 6 — Sex Disaggregation

Generated: 2026-03-18 | Reference period: Dec 2025 | Study period: Jan 2015 - Dec 2025

---

## Sex Composition by Status (Full Period 2015-2025, 132 months)

| Status | Total persons | Male | % | Female | % | Undefined | % |
|--------|--------------|------|---|--------|---|-----------|---|
| Total (0) | 262,814 | 160,857 | 61.2% | 101,630 | 38.7% | 327 | 0.1% |
| Not Located (7) | 89,850 | 69,871 | 77.8% | 19,843 | 22.1% | 136 | 0.2% |
| Located Alive (2) | 157,688 | 77,856 | 49.4% | 79,686 | 50.5% | 146 | 0.1% |
| Located Dead (3) | 15,343 | 13,175 | 85.9% | 2,123 | 13.8% | 45 | 0.3% |

Key finding — Located Alive near-parity: 49.4% male / 50.5% female. This contrasts sharply with Not Located (77.8% male) and Located Dead (85.9% male). Located Alive is the only status where female disappearances are the majority. This suggests recovery and location outcomes differ by sex.

Located Dead extreme male skew: 85.9% male, only 2,123 female cases over the full study period nationally (vs 13,175 male). This generates severe LISA power concerns.

---

## LISA Classifications by Sex — Dec 2025

### Not Located (status 7)

| Sex | HH | LL | HL | LH | NS |
|-----|----|----|----|----|-----|
| Male | 54 | 40 | 17 | 45 | 2,322 |
| Female | 37 | 48 | unknown | unknown | 2,326+ |
| Total | 53 | 37 | 17 | 45 | 2,326 |

Male Not Located has 1.46x more HH municipalities than female (54 vs 37).

### Located Dead (status 3)

| Sex | HH | LL |
|-----|----|----|
| Male | 3 | 2,333 |
| Female | 0 | 2,472 |
| Total | 7 | 2,327 |

CRITICAL: Female Located Dead has ZERO HH municipalities in Dec 2025. 2,472 of 2,478 municipalities are classified as LL for female Located Dead — this is a LISA artifact from near-zero counts everywhere, not an interpretable spatial pattern.

---

## Male vs Female HH Jaccard — Dec 2025

| Status | Male HH | Female HH | Intersection | Jaccard |
|--------|---------|-----------|--------------|---------|
| Total (0) | 76 | 52 | 44 | 0.5238 |
| Not Located (7) | 54 | 37 | 23 | 0.3382 |
| Located Alive (2) | 42 | 47 | 28 | 0.4590 |
| Located Dead (3) | 3 | 0 | 0 | 0.0000 |

Not Located (Jaccard=0.3382): Male and female HH geographies are moderately distinct. Male clustering is more spatially extensive (54 vs 37 munis). Located Alive (Jaccard=0.4590): Near-parity in case counts translates to substantial overlap in HH geography. Located Dead (Jaccard=0.0000): Zero overlap — driven entirely by absence of female LD HH clusters (LISA power failure, see below).

---

## Located Alive: Male vs Female Geographic Divergence (Dec 2025)

| Category | N munis | Primary region |
|----------|---------|----------------|
| Male HH | 42 | Centro (7), Norte (6), Norte-Occidente (1) — male-only |
| Female HH | 47 | Centro (11), Norte-Occidente (4), Norte (2) — female-only |
| Shared (both) | 28 | Centro: 18, Norte: 10 |
| Male-only | 14 | Centro: 7, Norte: 6, Norte-Occidente: 1 |
| Female-only | 19 | Centro: 11, Norte-Occidente: 4, Norte: 2, Centro-Norte: 1, Sur: 1 |

Key finding: The shared set (28 municipalities) is overwhelmingly CDMX metro (Centro: 18) plus Norte (10). Female-only HH municipalities lean Norte-Occidente (4 of 19) and Centro, while male-only HH municipalities lean Norte (6 of 14) and Centro. Female LA shows more Norte-Occidente presence than male.

---

## Statistical Power Assessment: Female Located Dead

| Metric | Value |
|--------|-------|
| Total female LD cases, 2015-2025 | 2,123 |
| Total observations (muni x month for status 3) | 327,096 |
| Mean female LD per municipality per month | 0.0065 |
| % zero muni-months for female LD | 99.42% |
| Maximum female LD in any single muni-month | 6 |
| Mean female LD per month (national total) | 16.1 |
| Min monthly national total | 2 |
| Max monthly national total | 33 |

Power assessment: LISA has NO interpretable power for female Located Dead.

With 99.42% of municipality-month observations being exactly zero for female Located Dead, monthly LISA is not meaningful. The signal is concentrated in perhaps 10-20 municipalities nationally, while the LISA algorithm operates on 2,478 units — 99.4% of which have zero monthly counts.

Recommendations for manuscript:
1. Report male Located Dead LISA results as the primary LD sex analysis.
2. Flag female Located Dead explicitly as insufficient power: mean 0.0065 cases/municipality/month, 99.42% zero muni-months.
3. Do NOT report female Located Dead LISA maps or HH counts as substantive findings — present as limitation.

---

## Summary for Paper

| Finding | Number |
|---------|--------|
| Located Alive sex parity | 49.4% male / 50.5% female |
| Not Located male skew | 77.8% male |
| Located Dead male skew | 85.9% male |
| LA male vs female Jaccard (Dec 2025) | 0.4590 |
| NL male vs female Jaccard (Dec 2025) | 0.3382 |
| Female LD power problem | YES — 0.0065 cases/muni/month, 99.42% zero |
