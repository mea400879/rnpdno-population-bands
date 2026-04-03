#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scrape_rnpdno_single_status.py
==============================

Single-status scraper for parallel execution.
Queries the RNPDNO portal by state × year × month, collecting
municipality-level sex-disaggregated counts from HTML tables
embedded in JSON API responses.

Includes state 33 ("Se desconoce") to capture records with
unresolvable geographic information (sentinel cvegeo=99998).

Usage:
    python scrape_rnpdno_single_status.py --status 0   # Total
    python scrape_rnpdno_single_status.py --status 7   # Desaparecidas y No Localizadas
    python scrape_rnpdno_single_status.py --status 2   # Localizadas con Vida
    python scrape_rnpdno_single_status.py --status 3   # Localizadas sin Vida

    # Single month (for validation):
    python scrape_rnpdno_single_status.py --status 0 --year 2015 --month 12

Run 4 terminals simultaneously for ~4x speedup.
Cookie must be set in .env as BROWSER_COOKIE=...
"""

import argparse
import json
import time
import logging
import calendar
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DIR  = PROJECT_ROOT / "data" / "raw" / "rnpdno_scraped"
LOG_DIR  = PROJECT_ROOT / "logs" / "scrapers"

BASE_URL = "https://versionpublicarnpdno.segob.gob.mx/SocioDemografico/TablaDetalle"

STATUS_CONFIG = {
    0: {"name": "total",
        "titulo": "PERSONAS DESAPARECIDAS, NO LOCALIZADAS Y LOCALIZADAS"},
    7: {"name": "desaparecidas_no_localizadas",
        "titulo": "PERSONAS DESAPARECIDAS Y NO LOCALIZADAS"},
    2: {"name": "localizadas_con_vida",
        "titulo": "PERSONAS LOCALIZADAS CON VIDA"},
    3: {"name": "localizadas_sin_vida",
        "titulo": "PERSONAS LOCALIZADAS SIN VIDA"},
}

YEAR_START = 2015
YEAR_END   = 2025

# States 1–32 + 33 ("Se desconoce") — required to capture cvegeo=99998 sentinels
ESTADOS = {
    1:  "Aguascalientes",       2:  "Baja California",
    3:  "Baja California Sur",  4:  "Campeche",
    5:  "Coahuila",             6:  "Colima",
    7:  "Chiapas",              8:  "Chihuahua",
    9:  "Ciudad de México",     10: "Durango",
    11: "Guanajuato",           12: "Guerrero",
    13: "Hidalgo",              14: "Jalisco",
    15: "México",               16: "Michoacán",
    17: "Morelos",              18: "Nayarit",
    19: "Nuevo León",           20: "Oaxaca",
    21: "Puebla",               22: "Querétaro",
    23: "Quintana Roo",         24: "San Luis Potosí",
    25: "Sinaloa",              26: "Sonora",
    27: "Tabasco",              28: "Tamaulipas",
    29: "Tlaxcala",             30: "Veracruz",
    31: "Yucatán",              32: "Zacatecas",
    33: "Se desconoce",
}

# Cookie loaded from .env — never hardcode
BROWSER_COOKIE = os.getenv("BROWSER_COOKIE", "")


# =============================================================================
# LOGGING
# =============================================================================

def setup_logging(status_name: str):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format=f"%(asctime)s [{status_name}] %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / f"scrape_{status_name}.log"),
            logging.StreamHandler(),
        ],
    )
    return logging.getLogger(__name__)


# =============================================================================
# HTTP
# =============================================================================

def create_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json; charset=UTF-8",
        "origin": "https://versionpublicarnpdno.segob.gob.mx",
        "referer": "https://versionpublicarnpdno.segob.gob.mx/Dashboard/Sociodemografico",
        "user-agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
        ),
        "x-requested-with": "XMLHttpRequest",
        "Cookie": BROWSER_COOKIE,
    })
    return s


def build_payload(id_estado: int, year: int, month: int, id_estatus: int) -> dict:
    last_day = calendar.monthrange(year, month)[1]
    return {
        "titulo": STATUS_CONFIG[id_estatus]["titulo"],
        "subtitulo": "POR MUNICIPIO",
        "idEstatusVictima": str(id_estatus),
        "fechaInicio": f"{year:04d}-{month:02d}-01",
        "fechaFin":    f"{year:04d}-{month:02d}-{last_day:02d}",
        "idEstado": str(id_estado),
        "idMunicipio": "0",
        "mostrarFechaNula": "0",
        "idColonia": "0",
        "idNacionalidad": "0",
        "edadInicio": "",
        "edadFin": "",
        "mostrarEdadNula": "0",
        "idHipotesis": "",
        "idMedioConocimiento": "",
        "idCircunstancia": "",
        "tieneDiscapacidad": "",
        "idTipoDiscapacidad": "0",
        "idEtnia": "0",
        "idLengua": "0",
        "idReligion": "",
        "esMigrante": "",
        "idEstatusMigratorio": "0",
        "esLgbttti": "",
        "esServidorPublico": "",
        "esDefensorDH": "",
        "esPeriodista": "",
        "esSindicalista": "",
        "esONG": "",
        "idHipotesisNoLocalizacion": "0",
        "idDelito": "0",
        "TipoDetalle": 3,
    }


def safe_post(session, payload, id_estado, year, month, logger, retries=4):
    backoff = 0.5
    for i in range(retries):
        try:
            resp = session.post(BASE_URL, data=json.dumps(payload), timeout=45)
            if resp.status_code == 200 and resp.content:
                try:
                    js = resp.json()
                    if js.get("Html"):
                        return resp
                except json.JSONDecodeError:
                    pass
            logger.warning(
                f"Retry {i+1}/{retries} — estado {id_estado} "
                f"({ESTADOS.get(id_estado,'?')}) {year}-{month:02d}"
            )
        except requests.Timeout:
            logger.warning(f"Timeout — estado {id_estado}")
        except requests.RequestException as e:
            logger.warning(f"Request error — estado {id_estado}: {e}")
        time.sleep(backoff)
        backoff *= 1.5
    return None


# =============================================================================
# PARSING
# =============================================================================

def extract_rows(html: str, id_estado: int, year: int, month: int,
                 id_estatus: int) -> list:
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for tr in soup.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 4:
            continue

        def to_int(x):
            x = x.strip().replace(",", "")
            return int(x) if x.isdigit() else 0

        municipio    = tds[0].get_text(strip=True)
        hombres      = to_int(tds[1].get_text())
        mujeres      = to_int(tds[2].get_text())
        indeterminado = to_int(tds[3].get_text())

        if hombres == 0 and mujeres == 0 and indeterminado == 0:
            continue

        rows.append({
            "municipio":          municipio,
            "hombres":            hombres,
            "mujeres":            mujeres,
            "indeterminado":      indeterminado,
            "total_personas":     hombres + mujeres + indeterminado,
            "id_estado":          id_estado,
            "estado":             ESTADOS.get(id_estado, ""),
            "anio":               year,
            "mes":                month,
            "id_estatus_victima": id_estatus,
        })
    return rows


# =============================================================================
# SCRAPING
# =============================================================================

def fetch_month(session, year: int, month: int, id_estatus: int,
                logger) -> pd.DataFrame:
    all_rows = []
    for id_estado in range(1, 34):        # 1–32 states + 33 (Se desconoce)
        payload = build_payload(id_estado, year, month, id_estatus)
        resp = safe_post(session, payload, id_estado, year, month, logger)
        if resp is None:
            continue
        try:
            html = resp.json().get("Html", "")
            if html:
                rows = extract_rows(html, id_estado, year, month, id_estatus)
                all_rows.extend(rows)
                if rows:
                    logger.info(
                        f"  Estado {id_estado:02d} "
                        f"({ESTADOS.get(id_estado,'?'):<20}): "
                        f"{sum(r['total_personas'] for r in rows):>4} persons"
                    )
        except Exception:
            continue
        time.sleep(0.5)
    return pd.DataFrame(all_rows)


def scrape_single_status(id_estatus: int, only_year: int = None,
                         only_month: int = None):
    config      = STATUS_CONFIG[id_estatus]
    status_name = config["name"]
    output_dir  = RAW_DIR / status_name
    output_dir.mkdir(parents=True, exist_ok=True)

    logger = setup_logging(status_name)
    logger.info("=" * 50)
    logger.info(f"SCRAPING: {status_name} (id={id_estatus})")
    if only_year:
        logger.info(f"Single month: {only_year}-{only_month:02d}")
    logger.info("=" * 50)

    if not BROWSER_COOKIE:
        logger.error("BROWSER_COOKIE not set in .env — cannot authenticate.")
        return

    session      = create_session()
    years        = [only_year] if only_year else range(YEAR_START, YEAR_END + 1)
    months       = [only_month] if only_month else range(1, 13)

    for year in years:
        for month in months:
            out_path = output_dir / f"rnpdno_{status_name}_{year}_{month:02d}.csv"
            if out_path.exists() and out_path.stat().st_size > 0 and not only_year:
                logger.info(f"Skip: {year}-{month:02d} (exists)")
                continue

            logger.info(f"\nDownloading {year}-{month:02d} ...")
            df = fetch_month(session, year, month, id_estatus, logger)

            if df.empty:
                logger.warning(f"Empty result: {year}-{month:02d}")
            else:
                df.to_csv(out_path, index=False)
                logger.info(
                    f"Saved: {out_path.name}  "
                    f"({len(df)} municipality rows, "
                    f"{df['total_personas'].sum()} persons)"
                )
            time.sleep(1.0)

    # Consolidate (skipped for single-month validation runs)
    if not only_year:
        logger.info("\nConsolidating all months...")
        consolidated_dir = RAW_DIR / "consolidated"
        consolidated_dir.mkdir(parents=True, exist_ok=True)
        dfs = []
        for fp in sorted(output_dir.glob(f"rnpdno_{status_name}_*.csv")):
            if fp.stat().st_size > 0:
                try:
                    dfs.append(pd.read_csv(fp))
                except Exception:
                    pass
        if dfs:
            df_all = pd.concat(dfs, ignore_index=True)
            out_pq = (consolidated_dir /
                      f"rnpdno_{status_name}_{YEAR_START}_{YEAR_END}.parquet")
            df_all.to_parquet(out_pq, index=False, compression="snappy")
            logger.info(f"Consolidated → {out_pq.name}  ({len(df_all):,} rows)")

    logger.info("DONE")


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="RNPDNO single-status scraper"
    )
    parser.add_argument(
        "--status", type=int, required=True, choices=[0, 2, 3, 7],
        help="Status ID: 0=Total, 7=Desap+NoLoc, 2=LocConVida, 3=LocSinVida",
    )
    parser.add_argument(
        "--year", type=int, default=None,
        help="Single year to scrape (for validation; requires --month)",
    )
    parser.add_argument(
        "--month", type=int, default=None,
        help="Single month to scrape (1–12; requires --year)",
    )
    args = parser.parse_args()

    if bool(args.year) != bool(args.month):
        parser.error("--year and --month must be used together")

    scrape_single_status(args.status, only_year=args.year, only_month=args.month)


if __name__ == "__main__":
    main()
