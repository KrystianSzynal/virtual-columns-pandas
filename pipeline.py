from pathlib import Path
import pandas as pd
from solution import add_virtual_column


def clean_sales_data(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df.copy()
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    # Remove repeated header row and summary TOTAL row
    order_id_clean = df["order_id"].astype(str).str.strip()
    is_repeated_header = order_id_clean == "Order ID"
    is_total_row = order_id_clean.str.upper() == "TOTAL"
    df = df[~(is_repeated_header | is_total_row)].copy()

    # Standardize text fields before deduplication
    df["order_id"] = df["order_id"].astype(str).str.strip()
    df["region"] = df["region"].astype(str).str.strip().str.title()
    df["product"] = df["product"].astype(str).str.strip()
    df["order_date"] = df["order_date"].astype(str).str.strip()

    # Drop exact duplicate order lines
    df = df.drop_duplicates(keep="first").copy()

    # Clean quantity (remove thousand-separator spaces; keep negative returns)
    qty_clean = df["quantity"].astype(str).str.replace(" ", "", regex=False).str.strip()
    df["quantity"] = pd.to_numeric(qty_clean, errors="raise").astype(int)

    # Clean unit_price (normalize decimal comma and impute missing from product price map)
    price_clean = (
        df["unit_price"]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .str.replace(" ", "", regex=False)
        .str.strip()
        .replace("", pd.NA)
    )
    df["unit_price"] = pd.to_numeric(price_clean, errors="coerce")
    product_price_map = (
        df.dropna(subset=["unit_price"])
        .groupby("product")["unit_price"]
        .first()
    )
    df["unit_price"] = df["unit_price"].fillna(df["product"].map(product_price_map))
    if df["unit_price"].isna().any():
        raise ValueError("Unable to impute missing unit_price for some products.")

    # Clean discount (empty string means no discount -> 0.0)
    disc_clean = (
        df["discount"]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .str.replace(" ", "", regex=False)
        .str.strip()
        .replace("", "0")
    )
    df["discount"] = pd.to_numeric(disc_clean, errors="raise").astype(float)

    return df.reset_index(drop=True)


def compute_revenue_by_region(clean_df: pd.DataFrame) -> pd.DataFrame:
    df_with_revenue = add_virtual_column(
        clean_df, "quantity * unit_price - discount", "revenue"
    )
    if df_with_revenue.empty:
        raise ValueError("Failed to compute 'revenue' column via add_virtual_column.")

    summary = (
        df_with_revenue.groupby("region", as_index=False)["revenue"]
        .sum()
        .sort_values("revenue", ascending=False)
        .reset_index(drop=True)
    )
    summary["revenue"] = summary["revenue"].round(2)
    return summary


def run_pipeline(
    input_path: str | Path = "sales.csv",
    output_path: str | Path = "revenue_by_region.csv",
) -> pd.DataFrame:
    raw_df = pd.read_csv(input_path, dtype=str, keep_default_na=False)
    clean_df = clean_sales_data(raw_df)
    summary_df = compute_revenue_by_region(clean_df)
    summary_df.to_csv(output_path, index=False)
    return summary_df


if __name__ == "__main__":
    result = run_pipeline()
    print(result.to_string(index=False))