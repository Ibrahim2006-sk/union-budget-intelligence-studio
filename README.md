# Union Budget Intelligence Studio

A polished, interactive Streamlit dashboard for exploring ten years of Indian Union Budget allocations
across ministries/departments. It includes animated ranking, trend lines, heatmaps, growth analysis,
treemap/pie composition, data quality checks, CSV downloads, and filters.

## Run on Windows

1. Extract this folder.
2. Open the folder in VS Code.
3. Open the integrated terminal and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
streamlit run app.py
```

Streamlit will show a local address, normally `http://localhost:8501`, and may open the browser.

## Data modes

- **Preview dashboard:** creates synthetic values only to preview the UI. These are clearly marked
  as DEMO and are NOT official Union Budget figures.
- **Upload official CSV:** upload a consolidated, validated CSV from the sidebar.
- **Use project CSV:** add `data/union_budget_allocations.csv` and choose that mode.

Required CSV columns:
- `sector`
- `financial_year` (e.g. `2015-16`)
- `allocation_crore` (number in ₹ crore)

Recommended additional columns:
- `estimate_type` (BE, RE, Actuals)
- `source` (official URL, document name and page/table)
- `notes`

Do not mix BE, RE and Actuals in one trend. Keep units consistent, validate ministry/department
classification changes, and avoid double-counting parent totals and departmental subtotals.

## Data folder
- `data/union_budget_allocations_TEMPLATE.csv`: blank template.
- `data/official_sources/`: downloaded official documents can be stored here.
- `data/raw_tables/`: raw table extracts.
- `outputs/`: reserved for saved outputs.

## Official source
https://www.indiabudget.gov.in/

Automatic extraction from PDFs is best effort. Review all extracted values against the official
source documents before citing any results.
