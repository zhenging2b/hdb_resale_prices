import pandas as pd


def readjust_price(
    df: pd.DataFrame,
    rpi: pd.DataFrame,
    target_year: int,
    target_quarter: int,
    price_col: str = "resale_price",
    month_col: str = "month",
) -> pd.DataFrame:
    """Rebase `price_col` to a target quarter's RPI.

    Adds a `Rescale_price_{target_year}_Q{target_quarter}` column computed as
    `price_col * (index_at_target_quarter / index_at_transaction_quarter)`, joining
    each row's transaction quarter against `rpi` (columns: Year, Quarter, Index).
    """
    target_index = rpi.loc[
        (rpi["Year"] == target_year) & (rpi["Quarter"] == target_quarter), "Index"
    ]
    if target_index.empty:
        raise ValueError(f"No RPI entry for {target_year} Q{target_quarter}")
    target_index = target_index.iloc[0]

    out = df.copy()
    out[month_col] = pd.to_datetime(out[month_col])

    quarter_keys = pd.DataFrame(
        {
            "Year": out[month_col].dt.year,
            "Quarter": out[month_col].dt.quarter,
        },
        index=out.index,
    )
    transaction_index = quarter_keys.merge(
        rpi[["Year", "Quarter", "Index"]], on=["Year", "Quarter"], how="left", validate="many_to_one"
    ).set_axis(out.index)["Index"]

    if transaction_index.isna().any():
        raise ValueError("Some transactions did not match an RPI quarter")

    new_col = f"Rescale_price_{target_year}_Q{target_quarter}"
    out[new_col] = out[price_col] * (target_index / transaction_index)

    return out

def get_storey_mid(val):
    start, end = val.split(' TO ')
    return (int(start) + int(end))/2

