"""
WP4 — Reference Audit
Parses all .tex files + references.bib to build:
  - audit/outputs/WP4_citation_map.csv
  - audit/outputs/WP4_bib_hygiene.csv
  - audit/outputs/WP4_results.json

Run: uv run python notebooks/audit/wp4_reference_audit.py
"""

import re
import json
import datetime
from pathlib import Path
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
MANUSCRIPT = ROOT / "manuscript"
BIB_FILE = MANUSCRIPT / "references.bib"
TEX_SECTIONS = MANUSCRIPT / "sections"
MAIN_TEX = MANUSCRIPT / "main.tex"
OUT_DIR = ROOT / "audit" / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TIMESTAMP = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ---------------------------------------------------------------------------
# 1. Parse BIB file
# ---------------------------------------------------------------------------
def parse_bib(bib_path: Path) -> dict:
    """Return dict keyed by bib key → {author, title, year, entry_type}."""
    text = bib_path.read_text(encoding="utf-8")

    # Split into entries
    # Each entry starts with @type{key,
    entry_pattern = re.compile(
        r'@(\w+)\s*\{\s*([^,\s]+)\s*,\s*(.*?)\n\}',
        re.DOTALL
    )

    bib = {}
    for m in entry_pattern.finditer(text):
        entry_type = m.group(1).lower()
        key = m.group(2).strip()
        body = m.group(3)

        def get_field(field_name, body_text):
            """Extract a field value from the bib entry body."""
            pat = re.compile(
                r'^\s*' + field_name + r'\s*=\s*\{(.*?)\}',
                re.IGNORECASE | re.DOTALL | re.MULTILINE
            )
            m2 = pat.search(body_text)
            if m2:
                return re.sub(r'\s+', ' ', m2.group(1).strip())
            # Try without braces (numeric year etc.)
            pat2 = re.compile(
                r'^\s*' + field_name + r'\s*=\s*([^,\n]+)',
                re.IGNORECASE | re.MULTILINE
            )
            m3 = pat2.search(body_text)
            if m3:
                return m3.group(1).strip().strip(',').strip()
            return ""

        author = get_field("author", body)
        title = get_field("title", body)
        year = get_field("year", body)
        # Clean up LaTeX in title
        title_clean = re.sub(r'\{([^}]*)\}', r'\1', title)
        title_clean = title_clean[:120]

        bib[key] = {
            "entry_type": entry_type,
            "author": author[:80] if author else "",
            "title": title_clean,
            "year": year,
        }
    return bib


# ---------------------------------------------------------------------------
# 2. Parse TEX files for cite commands
# ---------------------------------------------------------------------------
CITE_PATTERN = re.compile(
    r'\\(citep|citet|citeauthor|citeyear|cite)\*?\{([^}]+)\}'
)


def parse_tex_file(tex_path: Path) -> list[dict]:
    """Return list of citation records from a single tex file."""
    text = tex_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    records = []

    for lineno, line in enumerate(lines, start=1):
        for m in CITE_PATTERN.finditer(line):
            cite_type = m.group(1)
            keys_raw = m.group(2)
            # Keys may be comma-separated: \citet{vilalta_muggah_2016, vilalta_2021}
            keys = [k.strip() for k in keys_raw.split(",")]

            # Build context: surrounding sentence up to 120 chars
            # Use line content stripped of leading whitespace
            context = line.strip()[:120]

            for key in keys:
                if key:
                    records.append({
                        "cite_key": key,
                        "cite_type": cite_type,
                        "source_file": tex_path.name,
                        "line_number": lineno,
                        "context": context,
                    })
    return records


def parse_all_tex(sections_dir: Path, main_tex: Path) -> list[dict]:
    all_records = []
    tex_files = sorted(sections_dir.glob("*.tex")) + [main_tex]
    for f in tex_files:
        all_records.extend(parse_tex_file(f))
    return all_records


# ---------------------------------------------------------------------------
# 3. Build outputs
# ---------------------------------------------------------------------------
def build_citation_map(records: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(records)
    df = df[["cite_key", "source_file", "line_number", "cite_type", "context"]]
    return df


def build_bib_hygiene(bib: dict, cite_map: pd.DataFrame) -> pd.DataFrame:
    cited_keys = set(cite_map["cite_key"].unique())
    bib_keys = set(bib.keys())

    rows = []
    for key, meta in bib.items():
        if key in cited_keys:
            used_in = ", ".join(
                cite_map[cite_map["cite_key"] == key]["source_file"].unique().tolist()
            )
            status = "cited"
        else:
            used_in = ""
            status = "unused"
        rows.append({
            "key": key,
            "status": status,
            "used_in": used_in,
            "author": meta["author"],
            "title": meta["title"],
            "year": meta["year"],
        })

    # Add any keys cited in tex but missing from bib
    missing = cited_keys - bib_keys
    for key in sorted(missing):
        used_in = ", ".join(
            cite_map[cite_map["cite_key"] == key]["source_file"].unique().tolist()
        )
        rows.append({
            "key": key,
            "status": "MISSING_FROM_BIB",
            "used_in": used_in,
            "author": "",
            "title": "",
            "year": "",
        })

    df = pd.DataFrame(rows).sort_values(["status", "key"])
    return df


# ---------------------------------------------------------------------------
# 4. Build findings summary
# ---------------------------------------------------------------------------
def build_findings(cite_map: pd.DataFrame, bib_hygiene: pd.DataFrame,
                   bib: dict) -> dict:
    cited_keys = set(cite_map["cite_key"].unique())
    bib_keys = set(bib.keys())

    missing_from_bib = sorted(cited_keys - bib_keys)
    unused_in_bib = sorted(
        bib_hygiene[bib_hygiene["status"] == "unused"]["key"].tolist()
    )

    # Duplicate detection
    # baptista: baptista_2026 and baptista_davila_2026
    baptista_dup = {
        "keys": ["baptista_2026", "baptista_davila_2026"],
        "same_doi": "10.1016/j.puhe.2025.106107",
        "note": "Same paper — duplicate bib entries with different keys",
        "cited_keys": [k for k in ["baptista_2026", "baptista_davila_2026"] if k in cited_keys],
        "uncited_keys": [k for k in ["baptista_2026", "baptista_davila_2026"] if k not in cited_keys],
    }

    prieto_dup = {
        "keys": ["prieto_curiel_cartels_2023", "prieto_curiel_2023"],
        "same_doi": "10.1126/science.adh2888",
        "note": "Same paper — duplicate bib entries with different keys (prieto_curiel_2023 has full abstract)",
        "cited_keys": [k for k in ["prieto_curiel_cartels_2023", "prieto_curiel_2023"] if k in cited_keys],
        "uncited_keys": [k for k in ["prieto_curiel_cartels_2023", "prieto_curiel_2023"] if k not in cited_keys],
    }

    # le_cour_2020 line number in discussion.tex
    le_cour_rows = cite_map[cite_map["cite_key"] == "le_cour_2020"]
    le_cour_locations = le_cour_rows[["source_file", "line_number", "context"]].to_dict("records")

    # CED date check
    ced_bib = bib.get("CED_MEX_art34_2026", {})
    ced_note = ced_bib.get("title", "") + " | note field: " + str(ced_bib)

    return {
        "timestamp": TIMESTAMP,
        "n_citations_total": len(cite_map),
        "n_unique_cited_keys": len(cited_keys),
        "n_bib_entries": len(bib_keys),
        "n_missing_from_bib": len(missing_from_bib),
        "missing_from_bib": missing_from_bib,
        "n_unused_in_bib": len(unused_in_bib),
        "unused_in_bib": unused_in_bib,
        "duplicate_baptista": baptista_dup,
        "duplicate_prieto_curiel": prieto_dup,
        "le_cour_2020_locations": le_cour_locations,
        "ced_bib_entry": ced_bib,
    }


# ---------------------------------------------------------------------------
# 5. Main
# ---------------------------------------------------------------------------
def main():
    print(f"WP4 Reference Audit — {TIMESTAMP}")
    print("=" * 60)

    # Parse bib
    print(f"\n[1] Parsing {BIB_FILE.name} ...")
    bib = parse_bib(BIB_FILE)
    print(f"    Found {len(bib)} bib entries")
    for key in sorted(bib.keys())[:5]:
        print(f"    Sample: {key} ({bib[key]['year']}) — {bib[key]['title'][:60]}")

    # Parse tex
    print(f"\n[2] Parsing .tex files ...")
    records = parse_all_tex(TEX_SECTIONS, MAIN_TEX)
    print(f"    Found {len(records)} cite instances")

    # Build citation map
    cite_map = build_citation_map(records)
    unique_keys = set(cite_map["cite_key"].unique())
    print(f"    Unique cited keys: {len(unique_keys)}")

    # Build bib hygiene
    bib_hygiene = build_bib_hygiene(bib, cite_map)

    # Print key findings
    missing = sorted(unique_keys - set(bib.keys()))
    unused = sorted(bib_hygiene[bib_hygiene["status"] == "unused"]["key"].tolist())
    print(f"\n[3] Key findings:")
    print(f"    Missing from bib (cited but not defined): {missing}")
    print(f"    Unused bib entries: {unused}")

    # Duplicate check
    print(f"\n[4] Duplicate bib entries:")
    for pair, label in [
        (["baptista_2026", "baptista_davila_2026"], "baptista"),
        (["prieto_curiel_cartels_2023", "prieto_curiel_2023"], "prieto_curiel"),
    ]:
        in_bib = [k for k in pair if k in bib]
        in_tex = [k for k in pair if k in unique_keys]
        print(f"    {label}: in bib={in_bib}, cited in tex={in_tex}")

    # le_cour_2020 detail
    le_cour_rows = cite_map[cite_map["cite_key"] == "le_cour_2020"]
    print(f"\n[5] le_cour_2020 citations:")
    if len(le_cour_rows) == 0:
        print("    Not found in any tex file")
    else:
        for _, row in le_cour_rows.iterrows():
            print(f"    {row['source_file']} line {row['line_number']}: {row['context'][:80]}")

    # CED date check
    ced = bib.get("CED_MEX_art34_2026", {})
    print(f"\n[6] CED bib entry check:")
    print(f"    year={ced.get('year','')}  title={ced.get('title','')[:60]}")

    # prieto_curiel_2023 abstract verification
    print(f"\n[7] prieto_curiel_2023 abstract (for figure verification):")
    pc = bib.get("prieto_curiel_2023", {})
    # The abstract is stored in the bib but not extracted by our simple parser
    # (it's a non-standard field); check via raw text
    bib_text = BIB_FILE.read_text(encoding="utf-8")
    pc_abstract_match = re.search(
        r'prieto_curiel_2023.*?abstract\s*=\s*\{(.*?)\},',
        bib_text, re.DOTALL
    )
    if pc_abstract_match:
        abstract = pc_abstract_match.group(1)[:300]
        has_160k = "160,000" in abstract or "160000" in abstract
        has_350 = "350" in abstract
        print(f"    '160,000 to 185,000' in abstract: {has_160k}")
        print(f"    '350 to 370' in abstract: {has_350}")
    else:
        print("    abstract field not found in raw bib text")

    # Save outputs
    cite_map.to_csv(OUT_DIR / "WP4_citation_map.csv", index=False)
    bib_hygiene.to_csv(OUT_DIR / "WP4_bib_hygiene.csv", index=False)

    findings = build_findings(cite_map, bib_hygiene, bib)
    with open(OUT_DIR / "WP4_results.json", "w", encoding="utf-8") as f:
        json.dump(findings, f, indent=2, ensure_ascii=False)

    print(f"\n[8] Output files written:")
    print(f"    {OUT_DIR / 'WP4_citation_map.csv'}")
    print(f"    {OUT_DIR / 'WP4_bib_hygiene.csv'}")
    print(f"    {OUT_DIR / 'WP4_results.json'}")
    print(f"\nDone.")

    # Print citation map summary grouped by file
    print(f"\n=== Citation Map by File ===")
    for fname, grp in cite_map.groupby("source_file"):
        keys = sorted(grp["cite_key"].unique())
        print(f"  {fname} ({len(grp)} cite instances, {len(keys)} unique keys):")
        for k in keys:
            in_bib = "✓" if k in bib else "MISSING"
            print(f"      {k} [{in_bib}]")

    return findings


if __name__ == "__main__":
    main()
