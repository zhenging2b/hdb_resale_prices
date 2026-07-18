"""
Geocode the unique HDB block addresses in the merged dataset using the
OneMap Singapore Search API, then attach lat/lon back onto every transaction.

OneMap enforces a limit of 250 API calls per minute. We geocode only the
~10k *unique* addresses (not one call per transaction row), throttle
requests well under the limit, and cache results to disk incrementally so
the script is safe to interrupt and resume without re-querying addresses
already looked up.

Usage:
    python src/geocode_addresses.py

Output:
    data/geocoded_addresses.csv   (cache: address -> lat/lon, resumable)
    data/merged_resale_prices_geocoded.csv  (merged dataset + coordinates)
"""

import os
import time
from pathlib import Path

import pandas as pd
import requests

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MERGED_PATH = DATA_DIR / "merged_resale_prices.csv"
CACHE_PATH = DATA_DIR / "geocoded_addresses.csv"
OUTPUT_PATH = DATA_DIR / "merged_resale_prices_geocoded.csv"
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

ONEMAP_SEARCH_URL = "https://www.onemap.gov.sg/api/common/elastic/search"

# OneMap's limit is 250 calls/minute. Stay comfortably under it (200/min)
# to leave headroom for retries and clock drift.
CALLS_PER_MINUTE = 200
MIN_INTERVAL_SECONDS = 60.0 / CALLS_PER_MINUTE

REQUEST_TIMEOUT = 10
MAX_RETRIES = 3


def load_onemap_token() -> str | None:
    """Read ONEMAP_TOKEN from the environment, falling back to a local .env
    file (gitignored) with a line like `ONEMAP_TOKEN=<token>`."""
    token = os.environ.get("ONEMAP_TOKEN")
    if token:
        return token

    if ENV_PATH.exists():
        raw = ENV_PATH.read_bytes()
        if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
            text = raw.decode("utf-16")
        elif raw.startswith(b"\xef\xbb\xbf"):
            text = raw.decode("utf-8-sig")
        else:
            text = raw.decode("utf-8")

        for line in text.splitlines():
            line = line.strip()
            if line.startswith("ONEMAP_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")

    return None


ONEMAP_TOKEN = load_onemap_token()


CACHE_COLUMNS = [
    "address",
    "onemap_searchval",
    "onemap_blk_no",
    "onemap_road_name",
    "onemap_building",
    "onemap_address",
    "onemap_postal",
    "onemap_x",
    "onemap_y",
    "latitude",
    "longitude",
]


def load_cache() -> pd.DataFrame:
    if CACHE_PATH.exists():
        return pd.read_csv(CACHE_PATH)
    return pd.DataFrame(columns=CACHE_COLUMNS)


def append_to_cache(row: dict) -> None:
    df = pd.DataFrame([row])
    write_header = not CACHE_PATH.exists()
    df.to_csv(CACHE_PATH, mode="a", header=write_header, index=False)


def geocode_one(address: str) -> dict:
    params = {
        "searchVal": address,
        "returnGeom": "Y",
        "getAddrDetails": "Y",
        "pageNum": 1,
    }

    headers = {"Authorization": ONEMAP_TOKEN} if ONEMAP_TOKEN else {}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(
                ONEMAP_SEARCH_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT
            )
            if resp.status_code == 429:
                # Defensive fallback: honour the rate limit even if we
                # somehow exceed it (e.g. clock drift, retries).
                print("Rate limited by OneMap (429) - backing off 60s")
                time.sleep(60)
                continue
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results") or []
            if not results:
                return {col: (address if col == "address" else None) for col in CACHE_COLUMNS}
            top = results[0]
            return {
                "address": address,
                "onemap_searchval": top.get("SEARCHVAL"),
                "onemap_blk_no": top.get("BLK_NO"),
                "onemap_road_name": top.get("ROAD_NAME"),
                "onemap_building": top.get("BUILDING"),
                "onemap_address": top.get("ADDRESS"),
                "onemap_postal": top.get("POSTAL"),
                "onemap_x": float(top["X"]) if top.get("X") else None,
                "onemap_y": float(top["Y"]) if top.get("Y") else None,
                "latitude": float(top["LATITUDE"]),
                "longitude": float(top["LONGITUDE"]),
            }
        except (requests.RequestException, KeyError, ValueError) as exc:
            print(f"  attempt {attempt}/{MAX_RETRIES} failed for '{address}': {exc}")
            if attempt < MAX_RETRIES:
                time.sleep(2 * attempt)

    return {col: (address if col == "address" else None) for col in CACHE_COLUMNS}


def geocode_addresses(addresses: list[str]) -> None:
    cache = load_cache()
    already_done = set(cache["address"])
    todo = [a for a in addresses if a not in already_done]

    print(f"{len(already_done)} addresses already cached, {len(todo)} remaining")

    last_call = 0.0
    for i, address in enumerate(todo, start=1):
        elapsed = time.monotonic() - last_call
        if elapsed < MIN_INTERVAL_SECONDS:
            time.sleep(MIN_INTERVAL_SECONDS - elapsed)

        result = geocode_one(address)
        last_call = time.monotonic()
        append_to_cache(result)

        if i % 50 == 0 or i == len(todo):
            print(f"  geocoded {i}/{len(todo)} ({address}) -> "
                  f"({result['latitude']}, {result['longitude']})")


def main() -> None:
    print(f"OneMap token: {'found' if ONEMAP_TOKEN else 'NOT found - using anonymous requests'}")

    merged = pd.read_csv(MERGED_PATH)
    unique_addresses = sorted(merged["address"].dropna().unique())
    print(f"{len(unique_addresses)} unique addresses to geocode")

    geocode_addresses(unique_addresses)

    cache = load_cache().drop_duplicates(subset="address", keep="last")
    merged_geo = merged.merge(cache, on="address", how="left")

    missing = merged_geo["latitude"].isna().sum()
    print(f"{missing:,} / {len(merged_geo):,} rows without coordinates "
          f"({merged_geo['address'][merged_geo['latitude'].isna()].nunique()} unresolved addresses)")

    merged_geo.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved geocoded dataset to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
