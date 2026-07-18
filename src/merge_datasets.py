"""
Merge the 5 raw HDB resale flat price CSVs (data.gov.sg) into a single dataset.

The 4 source periods (1990-1999, 2000-Feb2012, Mar2012-Dec2014, Jan2015 onwards)
are split across 5 files because the Jan2015-onwards period itself was published
as two files (2015-2016, 2017 onwards). Columns are mostly consistent, except
`remaining_lease` which is only present (and inconsistently formatted, either
an integer number of years or a "X years Y months" string) in the two most
recent files. Since flat age / remaining lease can be derived consistently
from `lease_commence_date` and the transaction month for every row, we drop
the raw `remaining_lease` column and recompute it uniformly.

Output: data/merged_resale_prices.csv
"""

import re
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_PATH = DATA_DIR / "merged_resale_prices.csv"

SOURCE_FILES = [
    "Resale Flat Prices (Based on Approval Date), 1990 - 1999.csv",
    "Resale Flat Prices (Based on Approval Date), 2000 - Feb 2012.csv",
    "Resale Flat Prices (Based on Registration Date), From Mar 2012 to Dec 2014.csv",
    "Resale Flat Prices (Based on Registration Date), From Jan 2015 to Dec 2016.csv",
    "Resale flat prices based on registration date from Jan-2017 onwards.csv",
]

HDB_LEASE_YEARS = 99


def load_and_tag(filename: str) -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / filename)
    df["source_file"] = filename
    return df


def standardise(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Drop the raw remaining_lease column(s) - inconsistent format across files,
    # we recompute a uniform version below instead.
    df = df.drop(columns=[c for c in df.columns if c == "remaining_lease"])

    df["month"] = pd.to_datetime(df["month"], format="%Y-%m")
    df.loc[df["flat_type"] ==  "MULTI GENERATION", "flat_type"] = "MULTI-GENERATION"
    df["flat_type"] = df["flat_type"].str.upper().str.strip()
    df["flat_model"] = df["flat_model"].str.strip()
    df["town"] = df["town"].str.upper().str.strip()
    df["street_name"] = df["street_name"].str.upper().str.strip()
    df["block"] = df["block"].astype(str).str.upper().str.strip()

    df["lease_commence_date"] = df["lease_commence_date"].astype(int)
    df["flat_age_years"] = df["month"].dt.year - df["lease_commence_date"]
    df["remaining_lease_years"] = HDB_LEASE_YEARS - df["flat_age_years"]

    df["resale_price"] = df["resale_price"].astype(float)
    df["floor_area_sqm"] = df["floor_area_sqm"].astype(float)

    df["address"] = (df["block"] + " " + df["street_name"]).str.strip()
    df["address"] = df["address"].apply(lambda s: re.sub(r"\s+", " ", s))

    return df


def main() -> None:
    frames = [standardise(load_and_tag(f)) for f in SOURCE_FILES]
    merged = pd.concat(frames, ignore_index=True)

    merged = merged.sort_values(["month", "town", "street_name", "block"]).reset_index(drop=True)


    column_order = [
        "month",
        "town",
        "flat_type",
        "block",
        "street_name",
        "address",
        "storey_range",
        "floor_area_sqm",
        "flat_model",
        "lease_commence_date",
        "flat_age_years",
        "remaining_lease_years",
        "resale_price",
        "source_file",
    ]
    merged = merged[column_order]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(OUTPUT_PATH, index=False)

    print(f"Merged {len(SOURCE_FILES)} files into {len(merged):,} rows")
    print(f"Date range: {merged['month'].min().date()} to {merged['month'].max().date()}")
    print(f"Unique addresses: {merged['address'].nunique():,}")
    print(f"Saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
