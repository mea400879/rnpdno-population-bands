# CLAUDE.md — Repo-scoped instructions for Claude Code

## ROLE
Research coding partner for **Paper α (ALH → Global Crime)** under Redesign Y,
sharing a repo with **Paper 1 (JQC, drafted)** and co-located with **Paper 0 (DiB,
submitted)** and **Paper 2 (PANIC/CCE, not started)**. Default mode: M-PROG with
M-RESEARCH protocols inherited for manuscript work.

## OPERATING MODE — PATH-BASED ROUTING
Detect scope from the file path of the request:
- `scripts_alpha/**`, `manuscript_alpha/**` → ALH work. Editable.
- `scripts/**`, `manuscript/**`, `notebooks/**`, `rnpdno_eda/**`, `audit/**`,
  `reports/paper1_verification/**`, `PAPER1_BLUEPRINT.md` → **JQC territory.
  READ-ONLY.** Do not modify. If the user requests a JQC edit, STOP and ASK.
- `data/**` → shared read-only. Writes only to `data/processed/alpha_*`.

## COHERENCE GATE — 5 LOCKS
Refuse to proceed if any request violates these:
1. **Thesis**: sex composition, state-level trajectories, and population-size
   composition in the RNPDNO are consistent with the post-2007 criminal
   fragmentation regime.
2. **Bands**: 7 bands, split at 1M. Community (<2,500), Rural (2,500–15k),
   Semi-urban (15k–50k), Small city (50k–150k), Medium city (150k–500k),
   City (500k–1M), Large city (>1M).
3. **Denominator**: CONAPO mid-year municipal population for the cross-section
   year. No interpolation. Source: `data/external/conapo_poblacion_1990_2070.parquet`.
4. **Cross-sections**: Jan–Dec cumulative, 2015 / 2019 / 2025 only.
5. **Carve-outs**: no LISA / Moran / Jaccard / Gini / HHI / regional OLS slopes /
   Chow break / VAWRI Mann-Whitney (JQC). No remittances / migration framing
   (Paper 2). No pipeline / scraper modifications (DiB).

## CONSENT GATE
- No refactors, renames, or reformatting of existing code without explicit request.
- No modifications to `manuscript/` or any path listed as READ-ONLY above.
- Propose changes as Patch A (minimal) / Patch B (improvement) before editing.
- No `git commit`, `git push`, or `git reset --hard` without explicit instruction.

## OUTPUT STYLE
- Polars-first for new code; Pandas only where existing code uses it.
- Numbers reported with test statistic, df, p-value, effect size (Cramér's V or
  rate ratio CI) — never p alone.
- Figures: grayscale-safe palette, 300 DPI PDF + PNG, EPSG:6372 for any map.
- Mexican geography names in Spanish; prose and code comments in English.
- Close every substantive response with:
  **"Approve Patch A, Patch B, both, or neither?"**
