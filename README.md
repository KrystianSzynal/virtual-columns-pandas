# Virtual Columns & Sales Data Pipeline

Solution for the recruitment task implementing `add_virtual_column` and a data cleaning/aggregation pipeline for `sales.csv`.

## Setup

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

## Running the Pipeline and Tests

Generate `revenue_by_region.csv` from `sales.csv`:

```bash
python pipeline.py
```

Run all unit and integration tests (`test_virtual_column.py` and `test_custom.py`) with one command:

```bash
pytest
```

## Data Quality Issues Found in `sales.csv`

The raw file contains **1,507 data rows** (plus the main header), which resolve to **1,500 unique orders** (`SO-10001` through `SO-11500`) after cleaning:

| # | Issue | Affected Rows | How It Was Handled |
|---|-------|---------------|--------------------|
| 1 | **Non-compliant column headers** (`Quantity `, `Unit Price`, `Order ID`, `Order Date`) | All rows (schema) | Stripped whitespace and converted headers to `snake_case` (`quantity`, `unit_price`, etc.) so they satisfy the `^[a-zA-Z_]+$` validation rule in `add_virtual_column`. |
| 2 | **Repeated header row** (`Order ID,Region,...` inside the body) | 1 row (line 753) | Filtered out non-data rows where `order_id == "Order ID"`. |
| 3 | **Summary `TOTAL` row** at the end of the export | 1 row (line 1508) | Filtered out rows where `order_id == "TOTAL"` to avoid double-counting. |
| 4 | **Exact duplicate order rows** (`SO-10305`, `SO-10822`, `SO-10966`, `SO-11240`, `SO-11405`) | 5 duplicate rows (10 rows total in pairs) | Verified that all 7 columns in each duplicate pair are 100% identical and deduplicated with `drop_duplicates(keep="first")`. |
| 5 | **Inconsistent casing & whitespace in `Region`** (e.g., `' South'`, `'EAST'`, `'east  '`, `'west'`) | 15 order rows | Applied `.str.strip().str.title()` to standardize into the 5 valid regions (`North`, `South`, `Central`, `West`, `East`). |
| 6 | **Space thousand-separators in `Quantity`** (`1 762`, `1 745`, `1 371`, `1 427`) | 4 order rows | Removed spaces and parsed as integers (verified against the file's `TOTAL` quantity of `37,150`). |
| 7 | **Comma decimal separators in `Unit Price`** (e.g., `39,90`, `59,00`) | 7 order rows | Replaced `,` with `.` before numeric conversion. |
| 8 | **Missing `Unit Price` values** (`SO-10610`, `SO-11099`, `SO-11350`, `SO-11477`) | 4 order rows (5 incl. `TOTAL`) | Imputed from the fixed product catalog price derived from the remaining rows (`Printer paper = 21.00`, `Keyboard = 89.00`). |
| 9 | **Empty `Discount` cells** | 959 unique orders (963 raw rows) | Replaced empty strings with `0.0` per task specification. |
| 10 | **Negative `Quantity` values** (`-2` to `-5`) | 6 order rows | Kept as negative quantities (see Assumptions below). |

## Assumptions

- **Negative quantities represent returns/credit adjustments:** The 6 rows with negative `Quantity` (`-2` to `-5`) have valid `SO-*` order IDs, dates, products, unit prices, and no discounts. Rather than dropping or flipping their sign, they are preserved as returns that reduce regional revenue.
- **Large space-separated quantities are valid bulk orders:** Values like `1 762` sum together with the rest of the orders to `37,150`, matching the raw `TOTAL` footer row in `sales.csv`.
- **Single fixed price per product:** Every product in `sales.csv` maps 1:1 to a single constant `Unit Price` across all non-null rows, allowing deterministic imputation of missing prices without dropping rows.
- **Expression evaluation rules in `add_virtual_column`:** Supported expressions allow arbitrary chaining of `+`, `-`, and `*` across existing numeric columns (with standard operator precedence) while rejecting literals, unsupported operators, non-numeric columns, or column names outside `[a-zA-Z_]`.