# Singapore Jobs Analytics - Project Report

## 1. Business Case

### Problem Statement
Multiple stakeholders in Singapore's job market need data-driven insights but lack a unified platform for analysis. This project addresses three distinct business cases simultaneously:

**A. Talent Acquisition Teams (HR & Recruiters)**
- Need to identify in-demand roles and competitive salary benchmarks
- Struggle to track hiring trends and market competition
- Require forecasting to plan hiring pipelines 3-6 months ahead

**B. Career Coaches & Job Seekers**
- Lack visibility into salary expectations across roles and experience levels
- Need guidance on viable career transitions and growth pathways
- Require insights into skill requirements and market demand by sector

**C. Policy Analysts & Researchers**
- Need to analyze workforce trends and identify skills gaps
- Require industry growth patterns and employment type distributions
- Seek economic indicators and sector stability metrics for policy formulation

### Solution Delivered
A comprehensive analytics dashboard serving 1M+ job postings with:
- Interactive filtering across 43 job categories, 9 seniority levels, and 20 months of data
- Weighted average salary benchmarking and 6-month AI forecasting (Prophet)
- Career transition recommendations based on salary similarity and market demand
- Workforce trend analysis with 3-month moving averages, growth indicators, and stability metrics
- Static HTML dashboard for no-setup sharing

---

## 2. Data Handling & Process

### Data Architecture: Bronze-Silver-Gold

**Bronze Layer (Raw Data)**
- Source: SGJobData.csv (273 MB, 1,048,585 records)
- Timespan: October 2022 - May 2024 (20 months)
- 22 original fields including salary ranges, job categories, engagement metrics

**Silver Layer (Cleaned Data)**
- Removed 10 synthetic test rows (RANDOM_JOB_* with $23M salaries that inflated outlier thresholds)
- Removed 3,988 completely empty rows (all key fields NaN)
- Parsed JSON category structure: 43 unique categories, 37% multi-category jobs
- Implemented dual-category logic: ALL categories for filtering, PRIMARY category for aggregations
- Fixed seniority mapping: 250K rows corrected from "Unknown" to proper bucket (key mismatch: `Fresh/Entry Level` vs `Fresh / Entry Level`, missing `Non-Executive`)
- Winsorized salary outliers at 1st/99th percentiles (min/max clipped, average recomputed as (min+max)/2)
- Imputed missing salaries via 3-tier group median strategy (category × position level → category → global)
- Standardized text fields (Title Case for position levels and employment types)
- Created 16 engineered features including seniority levels, salary bands, engagement scores
- Output: 65.7 MB Parquet (1,044,587 rows, 38 columns)

**Gold Layer (Aggregated Metrics)**
- 8 pre-aggregated metric tables totaling 0.04 MB:
  1. `category_metrics.parquet` - Job count, median/mean salary, views/applications by category
  2. `position_metrics.parquet` - Metrics by seniority level
  3. `time_series.parquet` - Monthly job counts by category for trend analysis
  4. `company_metrics.parquet` - Top companies by posting volume
  5. `employment_metrics.parquet` - Job distribution by employment type
  6. `salary_distribution.parquet` - Percentile ranges by (category × position level)
  7. `category_trends.parquet` - Growth/decline trend indicators
  8. `job_forecasts.parquet` - 6-month Prophet forecasts for top categories
- Enables sub-second dashboard loading and GitHub-compatible deployment

### Data Quality Results

| Metric | Value | Status |
|--------|-------|--------|
| **Raw Rows** | 1,048,585 | Source |
| **Clean Rows** | 1,044,587 (99.62% preserved) | Excellent |
| **Rows Removed** | 3,998 (10 test + 3,988 empty) | Minimal loss |
| **Categories** | 43 (after removing Unknown) | Complete |
| **Seniority Unknown** | 0% (was 24% before fix) | Resolved |
| **Salary Coverage** | 100% (after imputation) | Complete |
| **Outliers Handled** | 19,862 (winsorized) | Addressed |
| **Text Inconsistencies** | Standardized across 4 fields | Resolved |
| **Data Quality Score** | 9/10 | High |

### Data Quality Documentation
- Comprehensive JSON report: `data/silver/data_quality_report.json`
- Jupyter notebook with before/after comparisons: `notebooks/02_data_quality_and_cleaning.ipynb`

### Technical Implementation

**ETL Pipeline (`data_pipeline.py`)**
1. **Bronze Validation**: Remove synthetic test rows (RANDOM_JOB_*) and completely empty rows
2. **Clean**: Date parsing, category JSON parsing, salary logic fixes, text standardization
3. **Fix Seniority**: Map all 9 position levels to Entry/Mid/Senior (0% Unknown after fix)
4. **Winsorize**: Clip min/max salaries at p1/p99, recompute average as (min+max)/2
5. **Impute**: 3-tier group median for missing salaries (category × level → category → global)
6. **Engineer**: 16 derived features (seniority, salary bands, engagement, competitiveness)
7. **Aggregate**: 8 gold metric tables including trends and 6-month forecasts
8. **Save**: Parquet format with Snappy compression (5.5x compression ratio)

**Quality Checks (`quality_checks.py`)**
- 5 validation categories: missing values, duplicates, outliers (IQR method), logic errors, text inconsistencies
- Severity assessment: LOW (issues < 1% of rows)
- Automated reporting to JSON for audit trail

---

## 3. Dashboard Description

### Architecture
- **Framework**: Streamlit multi-page app (Python 3.10+)
- **Charts**: Plotly (interactive, hover tooltips, responsive)
- **Data Loading**: Cached Gold layer metrics via `@st.cache_data` (sub-second load times)
- **Theme**: Dark theme with custom color scheme (config.toml)
- **Deployment**: Streamlit Cloud ready, also available as static HTML
- **File Size**: Total dashboard package < 1 MB (Gold layer only)

### Pages & Features

**Home Page (`app.py`)**
- Executive summary: 4 KPI cards (total jobs, categories, weighted avg salary, top companies)
- Top 15 job categories bar chart (colored by salary)
- Salary distribution by position level (horizontal bar chart)
- Hiring trends time series (monthly aggregation with trend line)
- Business case navigation cards with descriptions

**Page 1: Talent Acquisition Dashboard** 🎯
- **Purpose**: Help HR teams identify in-demand roles and competitive salaries
- **Filters**: Multi-select job categories (default: top 5 by volume)
- **KPIs**: Total roles, weighted avg salary, avg applications/job, categories analyzed
- **Visualizations**:
  - Top 15 in-demand roles (bar chart, colored by salary)
  - Salary vs demand bubble chart (normalized marker sizes 10-50px)
  - Monthly hiring trends with 3-month moving average (area chart)
  - 6-month AI forecast for top categories (Prophet)
- **Insights**: Most in-demand role, highest paying role, most competitive, avg experience
- **Table**: Detailed category breakdown with job count, salaries, applications, experience

**Page 2: Career Guide Dashboard** 🧭
- **Purpose**: Guide job seekers on career pathways and salary expectations
- **Personalization**: User profile (current level, career interests via sidebar)
- **KPIs**: Current level metrics (salary, available roles, typical experience)
- **Visualizations**:
  - Salary progression path (line chart across all levels)
  - Opportunities in selected interests (bar chart)
  - Salary comparison by interest area (bar chart)
  - Salary heatmap (category × position level)
- **Insights**: Career transition suggestions (similar salary ranges), high growth opportunities
- **Recommendations**: Best value career move, high demand sectors

**Page 3: Policy Insights Dashboard** 📊
- **Purpose**: Analyze workforce trends for policy formulation
- **KPIs**: Total market size, active sectors, weighted avg salary, active employers
- **Visualizations**:
  - Industry treemap (size = job count, color = salary)
  - Employment type distribution (pie + bar chart)
  - Hiring trends with 3-month moving average (time series)
  - HR budget spending by industry (horizontal bar)
  - Position level distribution (colored by salary)
  - Sector stability scatter plot (volatility vs avg monthly jobs)
  - Category growth/decline trend indicators
- **Policy Implications**: Computed insight cards (workforce development, skills gap, economic indicators)
- **Table**: Comprehensive sector metrics (jobs, salaries, views, applications, experience)

### Static HTML Dashboard
- Self-contained HTML file (`dashboard/singapore_jobs_dashboard.html`)
- 12 Plotly charts across 4 tabs (Talent Acquisition, Career Guide, Policy Insights, Data Tables)
- Dark theme, responsive layout, 0.1 MB file size
- Opens in any browser with no Python or setup required

### Smart Filtering Logic

**Multi-Category Handling**:
- **Filtering**: Jobs appear if ANY of their categories match selected filters
- **Aggregation**: Jobs counted once using PRIMARY category
- **Display**: All categories shown for each job

Example:
```
Job: "DevOps Engineer"
Categories: [IT (primary), Engineering, Telecommunications]

Filter: "Engineering"
→ Job appears in results ✓
→ Counted under "IT" in aggregations (primary category)
→ All 3 categories displayed in job details
```

### Performance Optimization
- `@st.cache_data` decorator on data loading functions
- Pre-aggregated Gold layer eliminates runtime calculations
- Parquet format for fast columnar access
- NaN-safe formatting with `pd.notna()` guards throughout
- Dashboard load time: < 1 second

---

## 4. Challenges & Learnings

### Key Challenges Encountered

**Challenge 1: Synthetic Test Rows Contaminating Data**
- **Issue**: 10 rows with IDs starting with RANDOM_JOB_* had salaries of ~$23M, inflating the p99 winsorization threshold and distorting all salary statistics.
- **Solution**: Added Bronze layer validation (Step 0) to filter rows by metadata_jobPostId prefix before any cleaning steps.
- **Learning**: Always validate raw data for test/synthetic records before statistical processing. Outlier handling can't fix bad data — it must be removed first.

**Challenge 2: Seniority Mapping Failure (24% → 0% Unknown)**
- **Issue**: 250,270 rows (24%) had "Unknown" seniority because the mapping keys didn't match the data. `Fresh / Entry Level` (with spaces around /) didn't match `Fresh/Entry Level` (no spaces). `Non-Executive` was missing entirely.
- **Solution**: Added exact key variants and missing levels to the seniority map. Verified by checking actual unique values in the data.
- **Learning**: Always compare mapping keys against actual data values — string matching is fragile with whitespace variations.

**Challenge 3: Multi-Category Jobs Creating Double-Counting**
- **Issue**: 37% of jobs have multiple categories. Naive aggregation double-counts these jobs.
- **Solution**: Implemented dual-purpose logic — filter by ALL categories, aggregate by PRIMARY category. Prevents jobs from being missed while maintaining accurate counts.
- **Learning**: Complex data structures require careful consideration of use cases (search vs analytics).

**Challenge 4: Winsorization Inconsistency**
- **Issue**: Initially winsorized min, max, and average salaries independently. This broke the relationship average = (min+max)/2.
- **Solution**: Winsorize only min and max, then recompute average as `(min + max) / 2`.
- **Learning**: When derived fields exist, always clip the source fields and recompute derivatives to maintain consistency.

**Challenge 5: Median-of-Medians Statistical Error**
- **Issue**: The "Market Salary" KPI was computed as median of per-category medians, giving equal weight to categories with 500 jobs and 100,000 jobs.
- **Solution**: Replaced with weighted average: `(median_salary × job_count).sum() / job_count.sum()`.
- **Learning**: Aggregating pre-aggregated statistics requires weighting by sample size.

**Challenge 6: File Size Exceeding GitHub Limits**
- **Issue**: Silver layer compressed to 65.7 MB (exceeds 50 MB ideal limit for GitHub).
- **Solution**: Dashboard loads exclusively from Gold layer (0.04 MB). Pre-aggregated metrics cover all planned analyses.
- **Learning**: Bronze-Silver-Gold architecture provides flexibility — can adapt deployment strategy based on file size constraints.

### Technical Insights

1. **Parquet Compression**: Achieved 5.5x compression (273 MB → 49.6 MB) vs CSV. Snappy codec provides good balance of speed and size.

2. **Prophet Forecasting**: Pre-computed 6-month forecasts for top categories and stored in Gold layer. Keeps dashboard lightweight while still providing predictive insights.

3. **Tooltip Styling**: Dark-themed dashboards require explicit tooltip styling — white backgrounds on dark themes create unreadable tooltips. Used `bgcolor="#2d2d2d"` with `font_color="white"`.

4. **Bubble Chart Sizing**: Raw job counts (500-100,000) produce unusable marker sizes. Min-max normalization to 10-50px range ensures visual clarity.

5. **Gold Layer Design**: Pre-aggregated metrics trade query flexibility for speed. 8 focused tables cover all 3 business cases without runtime computation.

---

## 5. Screenshots

_[Screenshots would be inserted here showing:]_

1. **Home Page**: Executive summary with KPIs and top categories chart
2. **Talent Acquisition Page**: In-demand roles and salary competitiveness bubble chart
3. **Career Guide Page**: Salary progression path and career transition recommendations
4. **Policy Insights Page**: Industry treemap and hiring trends with moving average

---

## Appendix: Technical Specifications

**Data Pipeline Execution Time**: ~45 seconds (1M+ rows)

**Dashboard Performance**:
- Initial load: < 1 second (cached)
- Filter update: < 0.5 seconds
- Chart rendering: Instant (Plotly)

**Technology Stack**:
- Python 3.10+
- Pandas 2.0+, NumPy 1.24+, PyArrow 14.0+
- Plotly 5.18+, Streamlit 1.29+
- Facebook Prophet 1.1.5 (pre-computed forecasts, not a runtime dependency)

**Deployment Options**:
- Streamlit Cloud (recommended): Deploy from GitHub, public URL
- Local: `pip install -r requirements.txt && streamlit run dashboard/app.py`
- Static HTML: Open `dashboard/singapore_jobs_dashboard.html` in any browser

**Repository Structure**:
```
Assignment 1/
├── .streamlit/
│   └── config.toml                      # Dark theme config
├── data/
│   ├── silver/
│   │   └── data_quality_report.json     # Data quality audit
│   └── gold/                            # Pre-aggregated metrics (0.04 MB)
│       ├── category_metrics.parquet
│       ├── position_metrics.parquet
│       ├── time_series.parquet
│       ├── company_metrics.parquet
│       ├── employment_metrics.parquet
│       ├── salary_distribution.parquet
│       ├── category_trends.parquet      # Growth/decline trends
│       └── job_forecasts.parquet        # 6-month Prophet forecasts
├── dashboard/
│   ├── app.py                           # Home page
│   ├── singapore_jobs_dashboard.html    # Static HTML version
│   └── pages/                           # 3 business case pages
├── src/
│   ├── data_pipeline.py                 # ETL pipeline
│   ├── quality_checks.py               # Data validation
│   └── data_discovery.py               # Initial profiling
├── notebooks/
│   ├── 01_data_discovery.ipynb
│   └── 02_data_quality_and_cleaning.ipynb
├── requirements.txt
├── README.md
├── REPORT.md                            # This document
└── PROJECT_PLAN.md
```

---

**Project Completion Date**: February 10, 2026
**Data Processing**: 1,048,585 rows → 1,044,587 clean records (99.62% preserved)
**Dashboard**: 3 business cases, 15+ interactive visualizations + static HTML
**Predictive Analytics**: 6-month Prophet forecasts for top job categories
