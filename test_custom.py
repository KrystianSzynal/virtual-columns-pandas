import pandas as pd
import pytest
from solution import add_virtual_column
from pipeline import clean_sales_data, compute_revenue_by_region, run_pipeline


# --- Part 1: add_virtual_column tests ---

def test_multi_column_expression_and_precedence():
    df = pd.DataFrame(
        {"quantity": [10, 4], "unit_price": [25.0, 15.5], "discount": [5.0, 2.0]}
    )
    result = add_virtual_column(df, "quantity * unit_price - discount", "revenue")
    assert result["revenue"].tolist() == [245.0, 60.0]


def test_original_dataframe_is_not_mutated():
    df = pd.DataFrame({"a": [2, 3], "b": [4, 5]})
    result = add_virtual_column(df, "a + b", "c")
    assert list(df.columns) == ["a", "b"]
    assert list(result.columns) == ["a", "b", "c"]


def test_invalid_existing_column_label_returns_empty():
    df = pd.DataFrame({"col_1": [1, 2], "col_two": [3, 4]})
    result = add_virtual_column(df, "col_1 + col_two", "valid_name")
    assert result.empty


def test_unsupported_operations_and_literals_return_empty():
    df = pd.DataFrame({"a": [10, 20], "b": [2, 5]})
    assert add_virtual_column(df, "a / b", "c").empty
    assert add_virtual_column(df, "a + 5", "c").empty
    assert add_virtual_column(df, "", "c").empty
    assert add_virtual_column(pd.DataFrame(), "a + b", "c").empty


def test_non_numeric_column_returns_empty():
    df = pd.DataFrame({"name": ["apple", "banana"], "price": [1, 2]})
    assert add_virtual_column(df, "name + price", "total").empty


# --- Part 2: pipeline tests ---

def test_clean_sales_data_handles_all_anomalies():
    raw = pd.DataFrame(
        {
            "Order ID": ["SO-1", "SO-1", "Order ID", "SO-2", "SO-3", "SO-4", "TOTAL"],
            "Region": [" south ", " south ", "Region", "EAST", "North", "west  ", ""],
            "Product": ["Mouse", "Mouse", "Product", "Mouse", "Keyboard", "Keyboard", ""],
            "Quantity ": ["1 000", "1 000", "Quantity ", "-2", "5", "3", "1006"],
            "Unit Price": ["29,50", "29,50", "Unit Price", "29.50", "89.00", "", ""],
            "Discount": ["10.00", "10.00", "Discount", "", "44,50", "", "54.50"],
            "Order Date": ["2026-01-01", "2026-01-01", "Order Date", "2026-01-02", "2026-01-03", "2026-01-04", ""],
        }
    )
    cleaned = clean_sales_data(raw)
    assert len(cleaned) == 4
    assert cleaned["region"].tolist() == ["South", "East", "North", "West"]
    assert cleaned["quantity"].tolist() == [1000, -2, 5, 3]
    assert cleaned["unit_price"].tolist() == [29.50, 29.50, 89.00, 89.00]
    assert cleaned["discount"].tolist() == [10.00, 0.00, 44.50, 0.00]


def test_end_to_end_pipeline_creates_output_csv(tmp_path):
    output_file = tmp_path / "revenue_by_region.csv"
    summary = run_pipeline(input_path="sales.csv", output_path=output_file)
    assert output_file.exists()
    assert list(summary.columns) == ["region", "revenue"]
    assert set(summary["region"]) == {"North", "South", "Central", "West", "East"}
    assert summary["revenue"].sum() == pytest.approx(2570247.03)