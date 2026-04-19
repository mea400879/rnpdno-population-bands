# WP6 Conclusion Cheat Sheet
**Verified values from CC-1 through CC-5. Plug in directly — no rounding beyond what is shown.**

---

## FINDING 1 — Centro is the dominant expanding region

| Metric | Value |
|---|---|
| Centro NL slope | +0.82 pct-pts/yr (HAC ***, Holm ***) |
| Centro LA slope | +0.58 pct-pts/yr (HAC ***, Holm **) |
| Centro LD slope | +0.16 pct-pts/yr (HAC ***, Holm ***) |
| Centro Total slope | +0.56 pct-pts/yr (HAC ***, Holm **) |
| Centro NL Poisson IRR | 1.264/yr (HAC ***) |
| Norte Total slope | +0.34 pct-pts/yr (HAC ***, Holm ***) |
| Norte LA slope | +0.46 pct-pts/yr (HAC ***, Holm ***) |
| Sur — all four statuses | ns under HAC and Holm |

---

## FINDING 2 — Centro-Norte Total is NOT significant after family-wise correction

| Metric | Value |
|---|---|
| Centro-Norte Total slope | −0.30 pct-pts/yr |
| Centro-Norte Total HAC p | 0.021 (*) |
| Centro-Norte Total Holm p | 0.231 (ns) |
| Centro-Norte NL slope | −0.30 pct-pts/yr (HAC **, Holm *) |
| Centro-Norte LA, LD | both ns at HAC and Holm |

---

## FINDING 3 — Bajío structural break: January 2017

| Metric | Value |
|---|---|
| Sup-Wald F (from WP3) | 78.125 (Andrews 5% CV ≈ 5.76) |
| Break date | January 2017 (idx = 24) |
| Total pre-break slope | −30.12 pct-pts/yr (HAC ***, Chow F = 78.0) |
| LA pre-break slope | −27.22 pct-pts/yr (HAC ***, Chow F = 107.0) |
| NL pre-break slope | −1.10 pct-pts/yr (HAC ns, Chow F = 4.4) |
| Total post-break slope | +1.66 pct-pts/yr (HAC *, OLS ***) |
| LA post-break slope | +2.12 pct-pts/yr (HAC **, OLS ***) |
| NL post-break slope | +1.12 pct-pts/yr (HAC ns, OLS **) |
| LD post-break slope | +0.88 pct-pts/yr (HAC *, OLS **) |
| Bajío NL full-period slope | +1.73 pct-pts/yr (HAC ***, Holm *) |

---

## FINDING 4 — Bajío municipality-level persistence (NL takeover)

| Municipality | NL pre | NL post | LA pre | LA post |
|---|---|---|---|---|
| Villagrán | 0.042 | 0.713 | 0.417 | 0.083 |
| Silao de la Victoria | 0.000 | 0.509 | 0.708 | 0.185 |
| Cortázar | 0.042 | 0.491 | 0.458 | 0.083 |
| Salamanca | 0.000 | 0.491 | 0.625 | 0.111 |
| Celaya | 0.000 | 0.389 | 0.375 | 0.000 |
| Guanajuato city | 0.000 | 0.343 | 0.667 | 0.185 |
| Irapuato | 0.000 | 0.241 | 0.667 | 0.065 |
| Jesús María (Ags) | 0.000 | 0.019 | 0.792 | 0.685 |
| Querétaro city | 0.000 | 0.019 | 0.542 | 0.000 |

*(Fractions = proportion of months classified BFS-HH; pre = 24 months Jan2015–Dec2016; post = 108 months Jan2017–Dec2025)*

---

## FINDING 5 — CED states (enforced disappearance)

| State | Total slope | HAC | NL slope | HAC |
|---|---|---|---|---|
| Estado de México | +1.76/yr | *** | +2.36/yr | *** |
| Nuevo León | +1.12/yr | *** | +0.44/yr | ** |
| Jalisco | −0.84/yr | * | −1.02/yr | ** |
| Guanajuato | −0.40/yr | ns | +0.75/yr | ** |
| Guanajuato LA | −0.57/yr | ns (p=0.40) | — | — |
| Tabasco | +0.15/yr | * | +0.21/yr | * |
| Nayarit | +0.10/yr | * | — | ns |
| Veracruz | +0.13/yr | ns | — | ns |
| Coahuila | all ns | — | — | — |

---

## FINDING 6 — Population size does not confound HH classification

| Pair | MW p | p > 0.50? | KS p |
|---|---|---|---|
| Total–NL | 0.682 | yes | 0.420 |
| Total–LA | 0.796 | yes | 0.820 |
| Total–LD | 0.415 | no | 0.493 |
| NL–LA | 0.905 | yes | 0.998 |
| NL–LD | 0.342 | no | 0.551 |
| LA–LD | 0.348 | no | 0.584 |

Correct claim: all six pairs p > 0.05; three of six pairs p > 0.50. LD median pop (437,916) is higher than Total/NL/LA (283–297k) but difference is not significant.

---

## CROSS-REFERENCE — Numbers that changed from manuscript

| # | Manuscript | Correct | Source |
|---|---|---|---|
| Break month | February 2017 | January 2017 | WP3 sup-Wald idx=24 |
| Post-break p (Total) | 0.046 | HAC p=0.042 (*) | CC-3 |
| Bajío NL full-period | +0.50/yr | +0.50/yr ✓ | CC-1 raw = +1.73 pct-pts/yr |
| Mann-Whitney threshold | "all p > 0.50" | all p > 0.05; three of six p > 0.50 | CC-5 |
| Guanajuato LA p | p < 0.001 | p = 0.40 (ns) | CC-4 / WP2-FIX |
| Centro-Norte Total | significant | ns after Holm | CC-1 Holm p = 0.231 |

---

*All values: INEGI 2020 populations (CC-5); BFS-filtered HH clusters (CC-1,2,5); raw LISA for Bajío corridor (CC-1,3,4); HAC bandwidth = 12 months; Holm across 24 tests (CC-1).*
