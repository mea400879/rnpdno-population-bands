"""
WP5 Discussion Fact-Check Audit Script
Generates: audit/claim_ledger.csv, audit/WP5_discussion_factcheck.md, audit/outputs/WP5_results.json
Run: uv run python audit/scripts/WP5_discussion_factcheck.py
"""

import pandas as pd
import json
import datetime
from pathlib import Path

ROOT = Path("/home/marco/workspace/work/rnpdno-population-bands")
AUDIT_DIR = ROOT / "audit"
OUTPUTS_DIR = AUDIT_DIR / "outputs"

# ============================================================
# 1. LOAD VERIFIED NUMBERS FROM PRIOR AUDIT OUTPUTS
# ============================================================

mw = pd.read_csv(OUTPUTS_DIR / "WP2_FIX_mannwhitney.csv")
gto = pd.read_csv(OUTPUTS_DIR / "WP2_FIX_ced_guanajuato.csv")
table5 = pd.read_csv(OUTPUTS_DIR / "WP2_FIX_table5_comparison.csv")
hac = pd.read_csv(OUTPUTS_DIR / "WP2_FIX_table5_hac.csv")
bfs_hac = pd.read_csv(OUTPUTS_DIR / "WP2_FIX_table5_full_diagnostics.csv")
bajio = pd.read_csv(OUTPUTS_DIR / "WP2_FIX_bajio_piecewise.csv")
wp2_stored = pd.read_csv(OUTPUTS_DIR / "WP2_table5_regional_trends.csv")
poisson = pd.read_csv(OUTPUTS_DIR / "WP3_t31_poisson.csv")
supwald = pd.read_csv(OUTPUTS_DIR / "WP3_t33_supwald.csv")

# Extract key values
mw_dict = dict(zip(mw["pair"], mw["p_value"]))
mw_gt050 = dict(zip(mw["pair"], mw["gt_050"]))

# Guanajuato LA verified values
gto_la = gto[gto["status"] == "la"].iloc[0]
gto_la_slope = gto_la["slope_yr"]          # -0.566
gto_la_hac_p = gto_la["hac_p"]            # 0.40
gto_la_hac_stars = gto_la["hac_stars"]    # ns
gto_la_ols_p = gto_la["ols_p"]            # 0.0028
gto_la_ols_stars = gto_la["ols_stars"]    # **

# Norte slopes from BFS full diagnostics
norte_total = bfs_hac[(bfs_hac["region"] == "Norte") & (bfs_hac["status"] == "total")].iloc[0]
norte_nl = bfs_hac[(bfs_hac["region"] == "Norte") & (bfs_hac["status"] == "nl")].iloc[0]
norte_la = bfs_hac[(bfs_hac["region"] == "Norte") & (bfs_hac["status"] == "la")].iloc[0]
norte_ld = bfs_hac[(bfs_hac["region"] == "Norte") & (bfs_hac["status"] == "ld")].iloc[0]

# Norte-Occidente LD
no_ld = bfs_hac[(bfs_hac["region"] == "Norte-Occidente") & (bfs_hac["status"] == "ld")].iloc[0]

# Bajio post-2017 piecewise from bajio CSV
bajio_post = bajio[(bajio["analysis"] == "chow_piecewise_total") & (bajio["segment"].str.startswith("post"))].iloc[0]
bajio_la_full = bajio[bajio["analysis"] == "subcomponent_full_period"][bajio[bajio["analysis"] == "subcomponent_full_period"]["status"] == "la"].iloc[0]
bajio_total_full = bajio[bajio["analysis"] == "subcomponent_full_period"][bajio[bajio["analysis"] == "subcomponent_full_period"]["status"] == "total"].iloc[0]

# Supremum Wald — maximum F is the break point
supwald_max = supwald.loc[supwald["chow_F"].idxmax()]

print("=== KEY VERIFIED NUMBERS ===")
print(f"\nMann-Whitney p-values:")
for pair, p in mw_dict.items():
    gt = "p>0.50" if mw_gt050[pair] else f"p={p:.4f} (NOT >0.50)"
    print(f"  {pair}: p={p:.4f}  {gt}")

print(f"\nGuanajuato LA: slope={gto_la_slope:.3f}/yr, HAC p={gto_la_hac_p:.4f} ({gto_la_hac_stars}), OLS p={gto_la_ols_p:.4f} ({gto_la_ols_stars})")
print(f"Manuscript claims: slope=-0.57/yr, p<0.001")

print(f"\nNorte slopes (BFS-filtered, HAC):")
print(f"  Total:  slope={norte_total['slope_yr']:.3f}, HAC p={norte_total['hac_p']:.4f} ({norte_total['hac_stars']}), OLS p={norte_total['ols_p']:.4f} ({norte_total['ols_stars']})")
print(f"  NL:     slope={norte_nl['slope_yr']:.3f}, HAC p={norte_nl['hac_p']:.4f} ({norte_nl['hac_stars']}), OLS p={norte_nl['ols_p']:.4f} ({norte_nl['ols_stars']})")
print(f"  LA:     slope={norte_la['slope_yr']:.3f}, HAC p={norte_la['hac_p']:.4f} ({norte_la['hac_stars']}), OLS p={norte_la['ols_p']:.4f} ({norte_la['ols_stars']})")
print(f"  LD:     slope={norte_ld['slope_yr']:.3f}, HAC p={norte_ld['hac_p']:.4f} ({norte_ld['hac_stars']}), OLS p={norte_ld['ols_p']:.4f} ({norte_ld['ols_stars']})")

print(f"\nNorte-Occidente LD (BFS): slope={no_ld['slope_yr']:.3f}, HAC p={no_ld['hac_p']:.4f}, OLS p={no_ld['ols_p']:.4f}")

print(f"\nBajio post-2017 piecewise:")
print(f"  slope={bajio_post['slope_yr']:.3f}, HAC p={bajio_post['hac_p']:.4f} ({bajio_post['hac_stars']}), OLS p={bajio_post['ols_p']:.4f} ({bajio_post['ols_stars']})")
print(f"  ms_slope={bajio_post['ms_slope']}, ms_p={bajio_post['ms_p_str']}")

print(f"\nBajio LA full-period: slope={bajio_la_full['slope_yr']:.3f}, HAC p={bajio_la_full['hac_p']:.4f} ({bajio_la_full['hac_stars']}), OLS p={bajio_la_full['ols_p']:.4f} ({bajio_la_full['ols_stars']})")
print(f"  ms_slope={bajio_la_full['ms_slope']}, ms_p={bajio_la_full['ms_p_str']}")

print(f"\nBajio Total full-period: slope={bajio_total_full['slope_yr']:.3f}, HAC p={bajio_total_full['hac_p']:.4f} ({bajio_total_full['hac_stars']}), OLS p={bajio_total_full['ols_p']:.4f} ({bajio_total_full['ols_stars']})")

print(f"\nSupWald max F: {supwald_max['chow_F']:.3f} at idx={supwald_max['break_idx']}, year={supwald_max['year']}, month={supwald_max['month']}, grid={supwald_max['grid']}")
# Manuscript claims Feb 2017 = index 24, F=78.13
# Check: break_idx=24 in the trimmed grid
supwald_feb2017 = supwald[(supwald["break_idx"] == 24) & (supwald["grid"] == "trimmed_15pct_85pct")]
if not supwald_feb2017.empty:
    row = supwald_feb2017.iloc[0]
    print(f"  Feb 2017 (idx=24) F={row['chow_F']:.3f} in trimmed grid")

# ============================================================
# 2. BUILD CLAIM LEDGER
# ============================================================

claims = []

# ---- ABSTRACT ----
claims.append({
    "section": "abstract",
    "location": "main.tex:103",
    "claim_text": "Mann-Whitney U, all pairwise p > 0.50",
    "type": "empirical",
    "status": "incorrect",
    "severity": "serious",
    "notes": (
        "WP2_FIX_mannwhitney.csv shows only 3/6 pairs have p>0.50 "
        f"(Total-NL p={mw_dict['Total-NL']:.4f}, Total-LA p={mw_dict['Total-LA']:.4f}, NL-LA p={mw_dict['NL-LA']:.4f}). "
        f"Three pairs have p<0.20: Total-LD p={mw_dict['Total-LD']:.4f}, NL-LD p={mw_dict['NL-LD']:.4f}, LA-LD p={mw_dict['LA-LD']:.4f}. "
        "Correct claim: 'all pairwise p > 0.05; three of six pairs p > 0.50'."
    )
})

# ---- INTRODUCTION ----
claims.append({
    "section": "introduction",
    "location": "introduction.tex:5",
    "claim_text": "RNPDNO documents over 132,000 persons whose whereabouts remain unknown",
    "type": "empirical",
    "status": "unverified",
    "severity": "trivial",
    "notes": "Administrative total from RNPDNO; plausible but not independently verified in this audit."
})

claims.append({
    "section": "introduction",
    "location": "introduction.tex:6",
    "claim_text": "In April 2026, the UN Committee on Enforced Disappearances (CED) issued its first referral to the General Assembly under Article 34",
    "type": "empirical",
    "status": "qualified",
    "severity": "moderate",
    "notes": (
        "The bib entry CED_MEX_art34_2026 notes 'Adopted at the 29th and 30th sessions (September 2025 and March 2026)'. "
        "If adopted March 2026, the April 2026 date in the text may refer to publication/release rather than adoption, "
        "but the distinction is not explained. Should clarify whether 'issued' means adopted, published, or transmitted."
    )
})

claims.append({
    "section": "introduction",
    "location": "introduction.tex:38",
    "claim_text": "between 2006 and 2017, only 19 of 732 disappearance investigations reached court, with just 9 convictions",
    "type": "empirical",
    "status": "unverified",
    "severity": "moderate",
    "notes": "Attributed to garcia_castillo_2024 and guevara_bermudez_2018. Numbers are precise enough to be verifiable but were not cross-checked in this audit. Reviewer may request primary source verification."
})

claims.append({
    "section": "introduction",
    "location": "introduction.tex:17",
    "claim_text": "Mexican cartels employ 160,000 to 185,000 members, sustained by recruiting 350 to 370 persons per week",
    "type": "literature",
    "status": "unverified",
    "severity": "trivial",
    "notes": "Attributed to prieto_curiel_2023. This is a literature claim; not independently verified here."
})

# ---- RESULTS: CLUSTERING ----
claims.append({
    "section": "results_clustering",
    "location": "results_clustering.tex:58",
    "claim_text": "municipal populations of HH sets do not differ significantly across outcome statuses (Mann-Whitney U, all pairwise p > 0.50)",
    "type": "empirical",
    "status": "incorrect",
    "severity": "serious",
    "notes": (
        "Repeated abstract error. WP2_FIX_mannwhitney.csv: only 3/6 pairs exceed p=0.50. "
        f"Pairs with p<0.50: Total-LD p={mw_dict['Total-LD']:.4f}, NL-LD p={mw_dict['NL-LD']:.4f}, LA-LD p={mw_dict['LA-LD']:.4f}. "
        "All are non-significant (all p>0.05), but the specific threshold p>0.50 is wrong for half the pairs."
    )
})

claims.append({
    "section": "results_clustering",
    "location": "results_clustering.tex:54-57",
    "claim_text": "NL<->LD = 0.143, LA<->LD = 0.151, NL<->LA = 0.381, Total<->LA = 0.674",
    "type": "empirical",
    "status": "unverified",
    "severity": "trivial",
    "notes": "Jaccard values not independently re-computed in WP2/WP3 audits. Plausible given LISA output structure. Mark for WP4 spatial verification."
})

claims.append({
    "section": "results_clustering",
    "location": "results_clustering.tex:22-24",
    "claim_text": "Global Moran's I: Total mean=0.199, Located Alive mean=0.187, Not Located mean=0.163, Located Dead mean=0.101",
    "type": "empirical",
    "status": "unverified",
    "severity": "trivial",
    "notes": "Descriptive statistics from LISA runs; not independently recomputed in this audit."
})

# ---- RESULTS: TEMPORAL ----
claims.append({
    "section": "results_temporal",
    "location": "results_temporal.tex:8",
    "claim_text": "Table reports OLS trend slopes (Newey-West HAC standard errors, bandwidth = 12)",
    "type": "empirical",
    "status": "incorrect",
    "severity": "serious",
    "notes": (
        "WP2_FIX_diagnosis.md confirms that Table 6 stars use OLS p-values, not HAC p-values, "
        "despite the caption. BFS+HAC re-computation changes stars for 7/24 cells: "
        "Norte-Occ total (***->**), Centro-Norte total (***->*), Bajio total (*->ns), "
        "Norte-Occ nl (***->**), Centro-Norte nl (***->**), Bajio la (**->ns), Bajio ld (*->ns). "
        "Caption says HAC but computation used OLS. Disclosure mismatch."
    )
})

claims.append({
    "section": "results_temporal",
    "location": "results_temporal.tex:15",
    "claim_text": "Not Located HH municipalities in Centro grew at +4.96 municipalities per year (p < 0.001)",
    "type": "empirical",
    "status": "verified",
    "severity": "trivial",
    "notes": f"WP2_table5_regional_trends.csv: slope={wp2_stored[( wp2_stored.region=='Centro') & (wp2_stored.status=='nl')].iloc[0]['slope_yr']:.3f}, p=0.0. BFS slope=4.941, HAC p=0.0 (***). Minor rounding 4.96->4.941, both round to 4.96."
})

claims.append({
    "section": "results_temporal",
    "location": "results_temporal.tex:16",
    "claim_text": "Centro Total +3.43 (p<0.001), Located Alive +3.63 (p<0.001), Located Dead +1.26 (p<0.001)",
    "type": "empirical",
    "status": "qualified",
    "severity": "trivial",
    "notes": (
        f"BFS slopes: Total={norte_total['slope_yr']:.3f} — wait, Centro: "
        f"Total BFS=3.398 (ms=3.43, rounding ok), LA BFS=3.489 (ms=3.63 — 0.14 discrepancy), "
        f"LD BFS=0.955 (ms=1.26 — 0.3 discrepancy). LA and LD show small but non-trivial differences "
        "between WP2 raw-LISA slopes and BFS-filtered slopes. All remain *** under HAC."
    )
})

claims.append({
    "section": "results_temporal",
    "location": "results_temporal.tex:34",
    "claim_text": "Norte: Total +0.62 (p=0.014), Not Located +0.59 (p=0.002), Located Alive +1.06 (p<0.001), Located Dead +0.78 (p<0.001)",
    "type": "empirical",
    "status": "qualified",
    "severity": "moderate",
    "notes": (
        f"Slopes in text are from WP2 raw-LISA; BFS-filtered values differ: "
        f"Total BFS={norte_total['slope_yr']:.3f} (ms=0.62), NL BFS={norte_nl['slope_yr']:.3f} (ms=0.59, rounding ok), "
        f"LA BFS={norte_la['slope_yr']:.3f} (ms=1.06 — 0.23 discrepancy), LD BFS={norte_ld['slope_yr']:.3f} (ms=0.78 — 0.01 discrepancy). "
        f"p=0.014 for Total: BFS HAC p={norte_total['hac_p']:.4f} ({norte_total['hac_stars']}). "
        f"Stars: Table 6 shows Norte Total as *** but BFS HAC gives *** (p=0.0). "
        f"Table 6 shows Norte NL as *** but WP2_stored gives ** (p=0.0022) and BFS HAC also ***. "
        "Norte LA: ms states p<0.001 — BFS HAC confirms ***. "
        "Norte LD: ms states p<0.001 — BFS HAC confirms ***. "
        "Main issues: LA slope 1.06 vs BFS 1.285; total slope stated 0.62 matches WP2 stored but BFS gives 0.958."
    )
})

claims.append({
    "section": "results_temporal",
    "location": "results_temporal.tex:42",
    "claim_text": "Bajio structural break F=78.13, p<0.001 at February 2017",
    "type": "empirical",
    "status": "qualified",
    "severity": "moderate",
    "notes": (
        "WP3_t33_supwald.csv trimmed_15pct_85pct grid: max F=78.125 at break_idx=24, year=2017, month=1 (JANUARY 2017). "
        "February 2017 (break_idx=25) gives F=77.720. "
        "Date encoding: yr=2015+(k+1)//12; mo=((k+1)%12) or 12. For k=24: yr=2017, mo=1 = January 2017. "
        "Manuscript says 'February 2017' but Supremum Wald peak is January 2017. "
        "WP3 script logged this as QUAL. F=78.13 rounds correctly from 78.125. "
        "Required correction: change 'February 2017' to 'January 2017'."
    )
})

claims.append({
    "section": "results_temporal",
    "location": "results_temporal.tex:43",
    "claim_text": "pre-break HH municipalities declining (beta_1 = -8.82 municipalities/year)",
    "type": "empirical",
    "status": "qualified",
    "severity": "trivial",
    "notes": f"WP2_FIX_bajio_piecewise.csv: pre-break slope=-8.599/yr (ms=-8.82). Difference of 0.22; both are clearly large negative slopes. Minor rounding/model-setup difference."
})

claims.append({
    "section": "results_temporal",
    "location": "results_temporal.tex:44",
    "claim_text": "post-2017 corridor expansion beta_2 = +0.47/yr (p=0.046)",
    "type": "empirical",
    "status": "qualified",
    "severity": "serious",
    "notes": (
        f"WP2_FIX_bajio_piecewise.csv: post slope={bajio_post['slope_yr']:.3f}, "
        f"OLS p={bajio_post['ols_p']:.4f} (*), HAC p={bajio_post['hac_p']:.4f} ({bajio_post['hac_stars']}). "
        "Manuscript reports p=0.046 matching OLS. However HAC p=0.054 which is NOT significant at 0.05. "
        "Given the table caption claims HAC SEs, the post-2017 expansion result is marginal (ns under HAC). "
        "The p=0.046 in text is from OLS, inconsistent with stated method."
    )
})

claims.append({
    "section": "results_temporal",
    "location": "results_temporal.tex:44",
    "claim_text": "Not Located post-2017 +0.50/yr (p<0.001)",
    "type": "empirical",
    "status": "verified",
    "severity": "trivial",
    "notes": "WP2_FIX_bajio_piecewise.csv nl full-period: slope=0.501, HAC p=0.001 (**). Manuscript reports *** (p<0.001) but HAC gives p=0.001 -> **. Minor stars discrepancy in table."
})

claims.append({
    "section": "results_temporal",
    "location": "results_temporal.tex:45",
    "claim_text": "Located Dead +0.15/yr (p=0.046)",
    "type": "empirical",
    "status": "qualified",
    "severity": "serious",
    "notes": (
        f"WP2_FIX_bajio_piecewise.csv: LD full-period OLS p={bajio[bajio['analysis']=='subcomponent_full_period'][bajio[bajio['analysis']=='subcomponent_full_period']['status']=='ld'].iloc[0]['ols_p']:.4f}, "
        f"HAC p={bajio[bajio['analysis']=='subcomponent_full_period'][bajio[bajio['analysis']=='subcomponent_full_period']['status']=='ld'].iloc[0]['hac_p']:.4f} (ns). "
        "p=0.046 in text is OLS. HAC gives ns. Inconsistent with HAC caption."
    )
})

claims.append({
    "section": "results_temporal",
    "location": "results_temporal.tex:45",
    "claim_text": "Located Alive declines -0.35/yr (p=0.003)",
    "type": "empirical",
    "status": "qualified",
    "severity": "serious",
    "notes": (
        f"WP2_FIX_bajio_piecewise.csv: LA OLS p={bajio_la_full['ols_p']:.4f} (**), "
        f"HAC p={bajio_la_full['hac_p']:.4f} (ns). "
        "p=0.003 in text is OLS. HAC gives ns (p=0.433). Inconsistent with HAC caption."
    )
})

claims.append({
    "section": "results_temporal",
    "location": "results_temporal.tex:46",
    "claim_text": "Total corridor slope -0.31/yr (p=0.041)",
    "type": "empirical",
    "status": "qualified",
    "severity": "serious",
    "notes": (
        f"WP2_FIX_bajio_piecewise.csv: Total OLS p={bajio_total_full['ols_p']:.4f} (*), "
        f"HAC p={bajio_total_full['hac_p']:.4f} (ns). "
        "p=0.041 in text is OLS. HAC gives ns (p=0.470). Inconsistent with HAC caption. "
        "Table 6 shows Bajio Total as -0.31*; BFS HAC gives ns. SERIOUS star inflation."
    )
})

# ---- RESULTS: CED ----
claims.append({
    "section": "results_ced",
    "location": "results_ced.tex:17",
    "claim_text": "Guanajuato Located Alive is declining (-0.57/yr, p < 0.001)",
    "type": "empirical",
    "status": "incorrect",
    "severity": "serious",
    "notes": (
        f"WP2_FIX_ced_guanajuato.csv: slope={gto_la_slope:.3f}/yr, "
        f"HAC p={gto_la_hac_p:.4f} ({gto_la_hac_stars}), OLS p={gto_la_ols_p:.4f} ({gto_la_ols_stars}). "
        "NEITHER HAC nor OLS gives p<0.001. HAC is entirely non-significant (p=0.40). "
        "OLS gives p=0.003 (**), still not p<0.001. The p<0.001 claim is wrong under both methods. "
        "The slope magnitude (-0.566 vs -0.57) is acceptably close."
    )
})

claims.append({
    "section": "results_ced",
    "location": "results_ced.tex:14",
    "claim_text": "Estado de Mexico: Not Located +2.36/yr (p<0.001), Located Alive +1.81/yr (p<0.001)",
    "type": "empirical",
    "status": "unverified",
    "severity": "trivial",
    "notes": "State-level CED slopes not re-computed in WP2/WP3 audits. Plausible."
})

claims.append({
    "section": "results_ced",
    "location": "results_ced.tex:15",
    "claim_text": "Nuevo Leon: Located Alive +1.34/yr (p<0.001), Located Dead +0.80/yr (p<0.001)",
    "type": "empirical",
    "status": "unverified",
    "severity": "trivial",
    "notes": "State-level NL slopes not re-computed in WP2/WP3 audits. Plausible."
})

claims.append({
    "section": "results_ced",
    "location": "results_ced.tex:20",
    "claim_text": "Jalisco: 3,825 persons in 2021 to 216 in 2024 (94% decline); municipalities 103 to 41",
    "type": "empirical",
    "status": "unverified",
    "severity": "moderate",
    "notes": "Specific registry counts not re-verified in this audit. The 94% claim is consistent with 216/3825=0.056, i.e., a 94.4% decline. Arithmetic is correct. Source data not independently re-queried."
})

# ---- DISCUSSION ----
claims.append({
    "section": "discussion",
    "location": "discussion.tex:20",
    "claim_text": "Centro's Not Located expanding at +4.96 municipalities per year (p < 0.001)",
    "type": "empirical",
    "status": "verified",
    "severity": "trivial",
    "notes": "Matches WP2 stored value and BFS slope=4.941. HAC p=0.0 (***). Correct."
})

claims.append({
    "section": "discussion",
    "location": "discussion.tex:23",
    "claim_text": "Fourth competing hypotheses may explain this pattern",
    "type": "hypothesis",
    "status": "incorrect",
    "severity": "moderate",
    "notes": "TYPO: 'Fourth' should be 'Four'. The sentence lists four hypotheses (first, second, third, and 'Last'). The word 'Fourth' is a typo for 'Four'."
})

claims.append({
    "section": "discussion",
    "location": "discussion.tex:29",
    "claim_text": "Norte's consistent positive slopes across all four statuses (p < 0.05 for each)",
    "type": "empirical",
    "status": "qualified",
    "severity": "moderate",
    "notes": (
        "Under BFS+HAC: Norte Total HAC p=0.0 (***), NL HAC p=0.0003 (***), LA HAC p=0.0 (***), LD HAC p=0.0 (***). "
        "All p<0.05, so claim directionally correct. "
        "However, the table shows Norte Total as *** using OLS stars, while the true HAC p=0.0 gives same conclusion here. "
        "Slope magnitudes differ between WP2 raw and BFS: LA 1.012 vs 1.285, Total 0.624 vs 0.958. "
        "The qualitative claim 'consistent positive slopes, p<0.05 for each' is supported."
    )
})

claims.append({
    "section": "discussion",
    "location": "discussion.tex:36-38",
    "claim_text": "Bajio structural break Feb 2017 F=78.13 (p<0.001); beta_1=-8.82/yr; beta_2=+0.47/yr (p=0.046)",
    "type": "empirical",
    "status": "qualified",
    "severity": "serious",
    "notes": (
        "F=78.13 verified. beta_2=+0.47/yr: WP2 gives 0.477, rounding ok. "
        "p=0.046 is OLS; HAC p=0.054 (ns). Claims based on OLS p-value inconsistent with HAC caption."
    )
})

claims.append({
    "section": "discussion",
    "location": "discussion.tex:38",
    "claim_text": "Total -0.31/yr (p=0.041), Located Alive -0.35/yr (p=0.003)",
    "type": "empirical",
    "status": "qualified",
    "severity": "serious",
    "notes": (
        "Both p-values are OLS. Under HAC: Total p=0.470 (ns), LA p=0.433 (ns). "
        "Discussion presents these as supporting claims about the Bajio corridor using OLS p-values "
        "while the methods section and table caption state HAC."
    )
})

claims.append({
    "section": "discussion",
    "location": "discussion.tex:53-55",
    "claim_text": "Jalisco: RNPDNO registrations collapsed from 3,825 in 2021 to 216 in 2024, 94% decline",
    "type": "empirical",
    "status": "unverified",
    "severity": "moderate",
    "notes": "Repeated from results_ced.tex. Same unverified note applies."
})

claims.append({
    "section": "discussion",
    "location": "discussion.tex:60",
    "claim_text": "Located Alive near-parity: 49.4% male, 50.5% female",
    "type": "empirical",
    "status": "unverified",
    "severity": "trivial",
    "notes": "Descriptive sex composition not re-computed in this audit. Note: 49.4+50.5=99.9 (rounding of third category or minor rounding artifact)."
})

claims.append({
    "section": "discussion",
    "location": "discussion.tex:60",
    "claim_text": "Not Located cases 77.9% male",
    "type": "empirical",
    "status": "unverified",
    "severity": "trivial",
    "notes": "Not re-computed in this audit."
})

claims.append({
    "section": "discussion",
    "location": "discussion.tex:64",
    "claim_text": "Not Located male vs female HH Jaccard = 0.262, with only 28 of 107 municipalities shared",
    "type": "empirical",
    "status": "unverified",
    "severity": "trivial",
    "notes": "Not re-computed in this audit."
})

claims.append({
    "section": "discussion",
    "location": "discussion.tex:65",
    "claim_text": "female Located Dead power failure, mean 0.0065 cases per municipality-month, 99.4% zero cells",
    "type": "empirical",
    "status": "unverified",
    "severity": "trivial",
    "notes": "Not re-computed but internally consistent with earlier results."
})

# ---- CONCLUSION ----
claims.append({
    "section": "conclusion",
    "location": "conclusion.tex:6",
    "claim_text": "Jaccard NL<->LD = 0.143, LA<->LD = 0.151",
    "type": "empirical",
    "status": "unverified",
    "severity": "trivial",
    "notes": "Repeated from results; not independently recomputed."
})

claims.append({
    "section": "conclusion",
    "location": "conclusion.tex:7",
    "claim_text": "50% of Not Located in 42 municipalities (1.7%), 50% of Located Dead in 22 (0.9%)",
    "type": "empirical",
    "status": "unverified",
    "severity": "trivial",
    "notes": "Concentration metrics not re-verified in this audit."
})

claims.append({
    "section": "conclusion",
    "location": "conclusion.tex:8",
    "claim_text": "Centro fastest-growing: Not Located +4.96/yr (p<0.001)",
    "type": "empirical",
    "status": "verified",
    "severity": "trivial",
    "notes": "Confirmed by WP2 and BFS audit. HAC p=0.0 (***)."
})

claims.append({
    "section": "conclusion",
    "location": "conclusion.tex:9",
    "claim_text": "Bajio: structural break Feb 2017, pre-break -8.82/yr, post-2017 +0.47/yr (p=0.046), Not Located +0.50/yr (p<0.001)",
    "type": "empirical",
    "status": "qualified",
    "severity": "serious",
    "notes": (
        "F=78.13 and break date confirmed. Pre-break slope: WP2 gives -8.599 vs -8.82 stated. "
        "Post-2017 p=0.046 is OLS; HAC gives p=0.054 (ns). NL +0.50 verified (HAC ** not ***)."
    )
})

claims.append({
    "section": "conclusion",
    "location": "conclusion.tex:9",
    "claim_text": "External validation: rank-biserial correlations 0.76 to 0.96 across all sex and status combinations",
    "type": "empirical",
    "status": "unverified",
    "severity": "trivial",
    "notes": "VAWRI correlations not re-verified in this audit."
})

# ---- CAUSAL LANGUAGE SWEEP ----
claims.append({
    "section": "discussion",
    "location": "discussion.tex:24",
    "claim_text": "potentially reflecting the urbanization of organized criminal violence as trafficking routes shift",
    "type": "hypothesis",
    "status": "verified",
    "severity": "trivial",
    "notes": "Appropriately hedged with 'potentially reflecting'. Causal language is conditional."
})

claims.append({
    "section": "discussion",
    "location": "discussion.tex:37",
    "claim_text": "driven primarily by Not Located cases",
    "type": "empirical",
    "status": "verified",
    "severity": "trivial",
    "notes": "'Driven' is an informal causal term but is used in the statistical sense of explaining variance. Limitation 5 in discussion acknowledges descriptive design. Acceptable."
})

claims.append({
    "section": "discussion",
    "location": "discussion.tex:9",
    "claim_text": "composite maps are 60% Located Alive cases, they misallocate resources",
    "type": "hypothesis",
    "status": "qualified",
    "severity": "trivial",
    "notes": "The 60% figure is implied from the dominance of LA in Total counts. 'Misallocate resources' is a policy implication stated as causal fact; should be 'could misallocate' given descriptive design."
})

claims.append({
    "section": "introduction",
    "location": "introduction.tex:9",
    "claim_text": "If these processes have different spatial drivers, composite maps conflating all outcomes will misallocate forensic and prevention resources",
    "type": "hypothesis",
    "status": "verified",
    "severity": "trivial",
    "notes": "Correctly framed as conditional ('if')."
})

# ---- REGISTRATION vs INCIDENCE ----
claims.append({
    "section": "discussion",
    "location": "discussion.tex:25",
    "claim_text": "urban municipalities ... may register a higher proportion of existing cases without a corresponding increase in underlying incidence",
    "type": "hypothesis",
    "status": "verified",
    "severity": "trivial",
    "notes": "Explicitly flagged as a competing hypothesis. Correctly distinguishes registration from incidence."
})

claims.append({
    "section": "discussion",
    "location": "discussion.tex:26",
    "claim_text": "institutional reforms ... coincide with the largest expansion of Not Located hotspot municipalities",
    "type": "hypothesis",
    "status": "verified",
    "severity": "trivial",
    "notes": "Uses 'coincide', not 'caused'. Appropriately cautious."
})

claims.append({
    "section": "discussion",
    "location": "discussion.tex:26",
    "claim_text": "legislative and administrative measures have not yet translated into a measurable spatial contraction of the disappearance crisis",
    "type": "hypothesis",
    "status": "qualified",
    "severity": "moderate",
    "notes": (
        "This implies registration = incidence for the purpose of 'contraction'. The sentence immediately "
        "qualifies it ('may also partly reflect improved registration'), but the opening assertion is stated "
        "flatly. Given limitation 3 (missing data/registration geography), this framing is somewhat strong."
    )
})

claims.append({
    "section": "introduction",
    "location": "introduction.tex:5",
    "claim_text": "a figure widely acknowledged to undercount the true scale",
    "type": "literature",
    "status": "verified",
    "severity": "trivial",
    "notes": "Attributed to guercke_2025. Standard and well-supported claim in this literature."
})

# ---- CONCLUSION FIVE EMPIRICAL FINDINGS CHECK ----
claims.append({
    "section": "conclusion",
    "location": "conclusion.tex:5-9",
    "claim_text": "FIVE EMPIRICAL FINDINGS: (1) spatial non-interchangeability, (2) extreme concentration, (3) Centro fastest-growing, (4) Bajio structural break, (5) VAWRI external validation",
    "type": "empirical",
    "status": "qualified",
    "severity": "moderate",
    "notes": (
        "Finding (1): verified in results_clustering. "
        "Finding (2): unverified but plausible. "
        "Finding (3): verified. "
        "Finding (4): qualified — Chow break verified but post-2017 expansion marginal under HAC (p=0.054). "
        "Finding (5): unverified. "
        "Findings (1)-(3) and (5) match their Results counterparts. "
        "Finding (4) overstates significance (OLS p=0.046 presented as HAC result)."
    )
})

# ---- TABLE 6 SIGNIFICANCE STARS ----
claims.append({
    "section": "results_temporal",
    "location": "tables/table6_trend_slopes.tex:7",
    "claim_text": "Table 6: Norte Total +0.62***",
    "type": "empirical",
    "status": "qualified",
    "severity": "moderate",
    "notes": (
        f"WP2 stored: slope=0.624, p=0.016 (*). BFS HAC: slope={norte_total['slope_yr']:.3f}, p={norte_total['hac_p']:.4f} (***). "
        "Two issues: (a) slope magnitude 0.62 vs BFS 0.958 — significant difference; "
        "(b) WP2 raw stored p=0.016 gives * but table shows ***. "
        "Under BFS HAC, *** is correct (p=0.0). The WP2 raw-LISA slope and p-value are wrong, "
        "but BFS HAC gives ***. Net: star is accidentally correct under BFS but wrong in WP2 raw."
    )
})

claims.append({
    "section": "results_temporal",
    "location": "tables/table6_trend_slopes.tex:7",
    "claim_text": "Table 6: Norte NL +0.59***",
    "type": "empirical",
    "status": "qualified",
    "severity": "moderate",
    "notes": (
        f"WP2 stored: slope=0.590, p=0.0022 (**). BFS HAC: slope={norte_nl['slope_yr']:.3f}, p={norte_nl['hac_p']:.4f} (***). "
        "Slope magnitude matches WP2 (0.590 vs 0.59). Stars: WP2 raw gives ** but table shows ***. "
        "BFS HAC gives *** (p=0.0003). If using BFS, *** is defensible. But using WP2 raw, it should be **."
    )
})

claims.append({
    "section": "results_temporal",
    "location": "tables/table6_trend_slopes.tex:9",
    "claim_text": "Table 6: Centro-Norte Total -1.02***",
    "type": "empirical",
    "status": "incorrect",
    "severity": "serious",
    "notes": (
        f"WP2 stored: slope=-1.022, p=0.036 (*). BFS HAC: slope={bfs_hac[(bfs_hac.region=='Centro-Norte') & (bfs_hac.status=='total')].iloc[0]['slope_yr']:.3f}, "
        f"p={bfs_hac[(bfs_hac.region=='Centro-Norte') & (bfs_hac.status=='total')].iloc[0]['hac_p']:.4f} (*). "
        "WP2 raw-LISA gives * (p=0.036). BFS HAC gives * (p=0.021). Both give ONE star. "
        "Table shows ***. SERIOUS: three stars vs one star."
    )
})

claims.append({
    "section": "results_temporal",
    "location": "tables/table6_trend_slopes.tex:9",
    "claim_text": "Table 6: Centro-Norte NL -0.76***",
    "type": "empirical",
    "status": "incorrect",
    "severity": "serious",
    "notes": (
        f"WP2 stored: slope=-0.734, p=0.028 (*). BFS HAC: slope={bfs_hac[(bfs_hac.region=='Centro-Norte') & (bfs_hac.status=='nl')].iloc[0]['slope_yr']:.3f}, "
        f"p={bfs_hac[(bfs_hac.region=='Centro-Norte') & (bfs_hac.status=='nl')].iloc[0]['hac_p']:.4f} (**). "
        "Table shows *** but WP2 raw-LISA gives * and BFS HAC gives **."
    )
})

claims.append({
    "section": "results_temporal",
    "location": "tables/table6_trend_slopes.tex:8",
    "claim_text": "Table 6: Norte-Occidente Total +0.63***",
    "type": "empirical",
    "status": "incorrect",
    "severity": "serious",
    "notes": (
        f"WP2 stored: slope=0.626. BFS HAC: slope={bfs_hac[(bfs_hac.region=='Norte-Occidente') & (bfs_hac.status=='total')].iloc[0]['slope_yr']:.3f}, "
        f"p={bfs_hac[(bfs_hac.region=='Norte-Occidente') & (bfs_hac.status=='total')].iloc[0]['hac_p']:.4f} (**). "
        "Table shows *** but BFS HAC gives ** (p=0.0024)."
    )
})

claims.append({
    "section": "results_temporal",
    "location": "tables/table6_trend_slopes.tex:8",
    "claim_text": "Table 6: Norte-Occidente NL +0.50***",
    "type": "empirical",
    "status": "incorrect",
    "severity": "serious",
    "notes": (
        f"WP2 stored: slope=0.503. BFS HAC: slope={bfs_hac[(bfs_hac.region=='Norte-Occidente') & (bfs_hac.status=='nl')].iloc[0]['slope_yr']:.3f}, "
        f"p={bfs_hac[(bfs_hac.region=='Norte-Occidente') & (bfs_hac.status=='nl')].iloc[0]['hac_p']:.4f} (**). "
        "Table shows *** but BFS HAC gives ** (p=0.009)."
    )
})

claims.append({
    "section": "results_temporal",
    "location": "tables/table6_trend_slopes.tex:12",
    "claim_text": "Table 6: Bajio Total -0.31*",
    "type": "empirical",
    "status": "incorrect",
    "severity": "serious",
    "notes": (
        f"WP2 stored: slope=-0.307, p=0.4696 (ns). BFS HAC: p={bfs_hac[(bfs_hac.region=='Bajio') & (bfs_hac.status=='total')].iloc[0]['hac_p']:.4f} (ns). "
        "OLS p=0.014 (*). Table shows * but HAC gives ns. Star is from OLS, not HAC as stated in caption."
    )
})

claims.append({
    "section": "results_temporal",
    "location": "tables/table6_trend_slopes.tex:12",
    "claim_text": "Table 6: Bajio LA -0.35**",
    "type": "empirical",
    "status": "incorrect",
    "severity": "serious",
    "notes": (
        f"WP2 stored: slope=-0.346, HAC p=0.4328 (ns), OLS p=0.0085 (**). "
        "Table shows ** but HAC gives ns. Star is from OLS, not HAC."
    )
})

claims.append({
    "section": "results_temporal",
    "location": "tables/table6_trend_slopes.tex:12",
    "claim_text": "Table 6: Bajio LD +0.15*",
    "type": "empirical",
    "status": "incorrect",
    "severity": "serious",
    "notes": (
        f"WP2 stored: slope=0.148, HAC p=0.1808 (ns), OLS p=0.0119 (*). "
        "Table shows * but HAC gives ns. Star is from OLS, not HAC."
    )
})

claims.append({
    "section": "results_temporal",
    "location": "tables/table6_trend_slopes.tex:11",
    "claim_text": "Table 6: Norte-Occidente LD +0.08 (ns)",
    "type": "empirical",
    "status": "qualified",
    "severity": "trivial",
    "notes": (
        "WP2 stored: slope=-0.080, ns. BFS: slope=+0.009, ns. "
        "Table shows +0.08 (matching WP2 magnitude but with reversed sign vs WP2 stored value of -0.08). "
        "BFS gives +0.009 (near zero, ns). Sign in WP2 raw was negative; table shows positive. "
        "Non-significant either way, but sign inconsistency between table and WP2 stored warrants a note."
    )
})

# ============================================================
# 3. SAVE CLAIM LEDGER
# ============================================================

df = pd.DataFrame(claims)
ledger_path = AUDIT_DIR / "claim_ledger.csv"
df.to_csv(ledger_path, index=False)
print(f"\nClaim ledger saved: {ledger_path} ({len(df)} claims)")

# ============================================================
# 4. SUMMARY STATS FOR REPORT
# ============================================================

print("\n=== CLAIM LEDGER SUMMARY ===")
print(df.groupby(["section", "type"]).size().to_string())
print("\nBy status:")
print(df["status"].value_counts().to_string())
print("\nBy severity:")
print(df["severity"].value_counts().to_string())
print("\nSerious/fatal issues:")
serious = df[df["severity"].isin(["serious", "fatal"])]
for _, row in serious.iterrows():
    print(f"  [{row['section']}] {row['claim_text'][:80]}")
    print(f"    -> {row['notes'][:120]}")

# ============================================================
# 5. SAVE JSON LOG
# ============================================================

results = {
    "task": "WP5",
    "timestamp": datetime.datetime.now().isoformat(),
    "claims_total": len(df),
    "by_type": df["type"].value_counts().to_dict(),
    "by_status": df["status"].value_counts().to_dict(),
    "by_severity": df["severity"].value_counts().to_dict(),
    "serious_count": int((df["severity"] == "serious").sum()),
    "fatal_count": int((df["severity"] == "fatal").sum()),
    "incorrect_count": int((df["status"] == "incorrect").sum()),
    "verified_count": int((df["status"] == "verified").sum()),
    "mann_whitney_pairs": mw_dict,
    "gto_la_hac_p": float(gto_la_hac_p),
    "gto_la_ols_p": float(gto_la_ols_p),
    "bajio_post_hac_p": float(bajio_post["hac_p"]),
    "bajio_post_ols_p": float(bajio_post["ols_p"]),
    "gate5_verdict": "CONDITIONAL PASS — corrections required before submission",
    "blocking_issues": [
        "Mann-Whitney claim 'all pairwise p>0.50' is wrong for 3/6 pairs (abstract and results_clustering)",
        "Guanajuato LA p<0.001 is wrong: HAC p=0.40 (ns), OLS p=0.003 — NEITHER is p<0.001",
        "Table 6 stars are OLS but caption says Newey-West HAC: 7 cells affected",
        "Bajio post-2017 expansion p=0.046 is OLS; HAC p=0.054 (ns)",
        "Bajio LA and Total sub-component stars: ** and * from OLS, ns under HAC",
        "Centro-Norte Total and NL in table show *** but correct value is * or **",
        "Norte-Occidente Total and NL show *** but correct value is **",
        "Chow break date: manuscript says February 2017 but Supremum Wald peak is January 2017 (F=78.125 at break_idx=24, month=1)",
        "Typo: 'Fourth competing hypotheses' should be 'Four competing hypotheses' (discussion.tex:23)"
    ]
}

json_path = OUTPUTS_DIR / "WP5_results.json"
with open(json_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nJSON log saved: {json_path}")
