# Singapore Jobs Analytics - Project Implementation Plan

## Context

This project fulfills a data coaching assignment to create a comprehensive analytics dashboard for ~1M Singapore job postings. The dataset (SGJobData.csv, 1,048,585 rows) contains job titles, companies, categories, salary ranges, position levels, and employment types. The goal is to address three business cases simultaneously:

1. **Talent Acquisition Teams**: Identify in-demand roles, skills, and competitive salary ranges
2. **Career Coaches/Job Seekers**: Guide on trending roles, required skills, salary expectations, and career transitions
3. **Policy Analysts**: Analyze workforce trends, skill gaps, and industry growth patterns

Additionally, the analysis includes **predictive insights** using Facebook Prophet to forecast future demand trends.

## Implementation Architecture

Following Bronze-Silver-Gold architecture:

```
Bronze Layer (Raw)         → Silver Layer (Cleaned)      → Gold Layer (Analytics)
SGJobData.csv             → cleaned_jobs.parquet       → 8 metric tables
                          → data_quality_report.json   → job_forecasts.parquet
```

## Critical Validations (Completed)

### Validation #1: Temporal Coverage ✅
- **Result**: 20 months of data (Oct 2022 - May 2024)
- **Decision**: Forecasting with Prophet is **FEASIBLE**

### Validation #2: File Size ✅
- **Result**: Silver layer 65.7 MB (exceeds 50MB GitHub limit)
- **Decision**: Dashboard uses **Gold layer only** (0.04 MB) — GitHub compatible

### Validation #3: Category Structure ✅
- **Result**: 43 unique categories, 37% multi-category jobs
- **Decision**: Use **PRIMARY category** for aggregations, **ALL categories** for filtering

### Validation #4: Bronze Layer Integrity ✅
- **Finding**: 10 synthetic test rows (RANDOM_JOB_* with $23M salaries) contaminating data
- **Finding**: 3,988 completely empty rows (all key fields NaN)
- **Finding**: Seniority mapping missed 250K rows (24%) due to key mismatches
- **Decision**: Added Bronze validation step to remove test/empty rows, fixed seniority map

## Multi-Category Handling Strategy

**Dual-Purpose Logic Implemented**:

| Use Case | Logic | Reason |
|----------|-------|--------|
| **Filtering/Search** | Check ALL categories | Job appears if ANY category matches |
| **Aggregation/Counting** | Use PRIMARY category only | Avoid double-counting |
| **Display** | Show ALL categories | Complete information |

## Data Quality Results

| Metric | Value | Status |
|--------|-------|--------|
| Raw Rows | 1,048,585 | Source |
| Clean Rows | 1,044,587 (99.62% preserved) | ✅ Excellent |
| Rows Removed | 3,998 (10 test + 3,988 empty) | ✅ Minimal |
| Categories | 43 (after removing Unknown) | ✅ Complete |
| Seniority Unknown | 0% (was 24% before fix) | ✅ Resolved |
| Salary Coverage | 100% (after imputation) | ✅ Complete |
| Outliers Handled | 19,862 winsorized | ✅ Addressed |
| Data Quality Score | 9/10 | ✅ High |

## Implementation Summary

### Steps Completed

**Step 1: Data Discovery ✅**
- Created `data_discovery.py` script
- Validated temporal coverage (20 months → forecasting feasible)
- Validated file size (65.7 MB Silver → Gold layer only for deployment)
- Parsed category structure (43 categories, multi-category handling)
- Generated validation report

**Step 2: Data Quality Assessment ✅**
- Created `quality_checks.py` module
- Implemented 5 quality checks:
  1. Missing values (MCAR/MAR/MNAR patterns)
  2. Duplicates (exact and fuzzy)
  3. Univariate outliers (IQR method)
  4. Logic errors (salary min > max, negative values)
  5. Text inconsistencies (case variations)
- Generated quality report: `data/silver/data_quality_report.json`
- Created quality notebook: `notebooks/02_data_quality_and_cleaning.ipynb`

**Step 3: Data Cleaning Pipeline ✅**
- Created `data_pipeline.py` ETL script
- Cleaning process:
  1. Remove synthetic test rows (RANDOM_JOB_* with $23M salaries)
  2. Remove completely empty rows (title + company + jobId all NaN)
  3. Drop null columns (occupationId 100% null)
  4. Parse dates (3 date fields)
  5. Parse categories JSON → primary + all_categories_list
  6. Fix seniority mapping (added `Fresh/Entry Level`, `Non-Executive` keys)
  7. Fix salary logic errors (swap min/max if reversed)
  8. Winsorize outliers at p1/p99 (clip min/max only, recompute average)
  9. Standardize text (Title Case for categorical fields)
  10. Impute missing salaries (3-tier group median: category × level → category → global)
  11. Remove duplicates (exclude list columns)
  12. Create date features (year, month, quarter)
- Output: Silver layer (65.7 MB, 1,044,587 rows, 38 columns)

**Step 4: Feature Engineering ✅**
- 16 engineered features created, including:
  - `seniority_level`: Entry/Mid/Senior mapping (0% Unknown after fix)
  - `salary_band`: Low/Medium/High/Very High/Premium
  - `experience_category`: No Exp/Entry/Mid/Senior/Expert
  - `application_rate`: Applications per view
  - `engagement_score`: Normalized metric (views + applications)
  - `is_multi_category`: Boolean flag
  - `salary_percentile`: Rank within category
  - `salary_competitiveness`: Below/At/Above market

**Step 5: Gold Layer Creation ✅**
- 8 pre-aggregated metric tables (0.04 MB total):
  1. `category_metrics.parquet` - Job count, salaries, applications by category
  2. `position_metrics.parquet` - Metrics by seniority level
  3. `time_series.parquet` - Monthly job counts by category
  4. `company_metrics.parquet` - Top companies by posting volume
  5. `employment_metrics.parquet` - Job distribution by employment type
  6. `salary_distribution.parquet` - Percentiles by (category × position level)
  7. `category_trends.parquet` - Growth/decline trend indicators
  8. `job_forecasts.parquet` - 6-month Prophet forecasts for top categories

**Step 6: Streamlit Dashboard ✅**
- Multi-page app with 4 pages:
  1. **Home (app.py)**: Executive summary, KPIs, top categories, trends
  2. **Talent Acquisition**: In-demand roles, salary competitiveness, hiring trends, AI forecast
  3. **Career Guide**: Salary progression, career transitions, personalized recommendations
  4. **Policy Insights**: Industry treemap, employment types, workforce trends, stability metrics
- Dark theme with custom styling (`.streamlit/config.toml`)
- NaN-safe formatting with `pd.notna()` guards
- Weighted average salary (not median-of-medians)
- Normalized bubble chart markers (10-50px range)
- Styled tooltips for dark theme contrast

**Step 7: Static HTML Dashboard ✅**
- `dashboard/singapore_jobs_dashboard.html`
- 12 Plotly charts across 4 tabs
- Self-contained with Plotly CDN, dark theme
- 0.1 MB file size, opens in any browser

**Step 8: Documentation ✅**
- `README.md`: Setup instructions, project structure, features, deployment options
- `REPORT.md`: Business case, data handling, dashboard description, challenges & learnings
- `PROJECT_PLAN.md`: This document
- `data/silver/data_quality_report.json`: Comprehensive quality audit
- `notebooks/02_data_quality_and_cleaning.ipynb`: Quality report with before/after comparisons

**Step 9: GitHub Deployment ✅**
- Repository: `tsantoso79/singapore-jobs-analytics`
- `.gitignore` excludes raw CSV and Silver layer
- Gold layer (0.04 MB) included for dashboard operation
- Streamlit Cloud compatible (requirements.txt, config.toml)

**Step 10: Quality Assurance ✅**
- Multiple critic agent reviews (Opus model)
- Fixed: NameError in Policy Insights, tooltip contrast, bubble chart overflow
- Fixed: Median-of-medians → weighted average salary
- Fixed: Hardcoded selectbox index, dead variables, NaN formatting
- Data pipeline audit: Verified salary_type (all Monthly), no negative salaries
- Bronze layer audit: Removed test rows, empty rows, fixed seniority mapping

## Technology Stack

**Dashboard Dependencies** (Streamlit Cloud):
- Python 3.10+
- Pandas 2.0+, NumPy 1.24+, PyArrow 14.0+
- Plotly 5.18+, Streamlit 1.29+

**Pipeline Dependencies** (development only):
- Facebook Prophet 1.1.5 (pre-computed forecasts in Gold layer)
- Scikit-learn 1.3.2 (used in pipeline only)
- Matplotlib, Seaborn (notebooks only)

## File Size Strategy

| Layer | Size | Included in Repo |
|-------|------|------------------|
| Bronze (SGJobData.csv) | 273 MB | ❌ Too large |
| Silver (cleaned_jobs.parquet) | 65.7 MB | ❌ Exceeds 50MB limit |
| Gold (8 metric files) | 0.04 MB | ✅ GitHub compatible |
| HTML Dashboard | 0.1 MB | ✅ Included |

**Dashboard Strategy**: Load exclusively from Gold layer (pre-aggregated metrics)

## Key Design Decisions

1. **Bronze Validation First**: Remove synthetic/empty rows before any statistical processing to prevent contamination of percentile calculations

2. **Seniority Map Verification**: Compare mapping keys against actual data values to catch whitespace and naming mismatches

3. **Winsorize Sources, Recompute Derivatives**: Clip only min/max salaries, then recompute average to maintain mathematical consistency

4. **Weighted Aggregation**: Use `(metric × count).sum() / count.sum()` instead of median-of-medians for market-level statistics

5. **Multi-Category Logic**: Dual-purpose (filter by ALL, aggregate by PRIMARY) to balance discoverability and accuracy

6. **Gold Layer Approach**: Pre-aggregate all metrics including forecasts for sub-second dashboard performance

7. **Pre-computed Forecasting**: Run Prophet at pipeline time, store results in Gold layer to avoid runtime dependency

## Success Metrics

✅ All 1M+ rows processed through Bronze-Silver-Gold pipeline
✅ Data quality: 99.62% preserved (3,998 rows removed: 10 test + 3,988 empty)
✅ Seniority mapping: 0% Unknown (was 24%)
✅ Dashboard serves 3 business personas with distinct views
✅ Predictive insights: 6-month Prophet forecasts for top categories
✅ Multi-category filtering works correctly (37% of jobs affected)
✅ Interactive filters with sub-second response time
✅ Multiple Opus-level critic reviews completed
✅ Complete documentation (README, REPORT, PLAN, quality notebook)
✅ GitHub-compatible deployment (< 1 MB total Gold layer + HTML)
✅ Static HTML dashboard for no-setup sharing
✅ Dashboard tested and working (Streamlit launches successfully)

## Future Enhancements

1. **Skill Extraction**: NLP on job descriptions to extract required skills and technologies
2. **Advanced Filters**: Salary range slider, date range picker, cascading filter logic
3. **Real-Time Updates**: Integrate with live job posting APIs for current data
4. **Export Functionality**: Allow users to download filtered datasets as CSV/Excel
5. **User Authentication**: Personalized dashboards with saved filter preferences

## Project Completion Status

**Data Processing**: 1,048,585 rows → 1,044,587 clean records (99.62% preserved)
**Dashboard**: 3 business cases, 15+ interactive visualizations + static HTML
**Predictive Analytics**: 6-month Prophet forecasts for top job categories
**Quality Assurance**: Multiple Opus-level reviews, all critical issues resolved

**Status**: ✅ **DEPLOYED TO GITHUB**
