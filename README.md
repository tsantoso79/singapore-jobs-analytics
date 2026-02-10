# Singapore Jobs Analytics Dashboard

**1M+ Job Postings | 3 Business Cases | Interactive Analytics**

A comprehensive data analytics dashboard analyzing Singapore's job market across 20 months (Oct 2022 - May 2024). Built to serve talent acquisition teams, career coaches, and policy analysts with real-time insights.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.29+-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

## Quick Start

### Prerequisites
- Python 3.10 or higher
- pip package manager

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/tsantoso79/singapore-jobs-analytics.git
cd singapore-jobs-analytics
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the data pipeline** (optional - Gold layer already provided)
```bash
python src/data_pipeline.py
```

4. **Launch the dashboard**
```bash
streamlit run dashboard/app.py
```

5. **Access the dashboard**
Open your browser to `http://localhost:8501`

### Static HTML Version
For a no-setup experience, open `dashboard/singapore_jobs_dashboard.html` directly in any browser.

---

## Project Structure

```
Assignment 1/
├── .streamlit/
│   └── config.toml                      # Streamlit Cloud theme config
├── data/
│   ├── silver/
│   │   └── data_quality_report.json     # Data quality audit report
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
│   ├── app.py                           # Main dashboard (home page)
│   ├── singapore_jobs_dashboard.html    # Static HTML version (no setup)
│   └── pages/
│       ├── 1_🎯_Talent_Acquisition.py   # HR & Recruiter insights
│       ├── 2_🧭_Career_Guide.py         # Job seeker guidance
│       └── 3_📊_Policy_Insights.py      # Workforce analytics
├── src/
│   ├── data_pipeline.py                 # ETL pipeline (Bronze -> Silver -> Gold)
│   ├── quality_checks.py               # Data quality validation
│   └── data_discovery.py               # Initial data profiling
├── notebooks/
│   ├── 01_data_discovery.ipynb          # Initial exploration
│   └── 02_data_quality_and_cleaning.ipynb  # Quality report with before/after
├── requirements.txt                     # Python dependencies
├── README.md                            # This file
├── REPORT.md                            # Detailed project report
├── PROJECT_PLAN.md                      # Implementation plan
└── SGJobData.csv                        # Raw data (not in repo - too large)
```

---

## Features

### Three Business Cases Served

**1. Talent Acquisition Dashboard** 🎯
- Identify top in-demand roles and competitive salary ranges
- Track hiring trends over time with 3-month moving averages
- 6-month AI forecast (Prophet) for top categories
- Filter by job categories with interactive visualizations

**2. Career Guide Dashboard** 🧭
- Personalized salary progression paths
- Career transition recommendations based on salary similarity
- Compare opportunities across interest areas
- Salary heatmaps by category and seniority

**3. Policy Insights Dashboard** 📊
- Workforce trend analysis with moving averages
- Industry distribution treemaps
- HR budget spending analysis by industry
- Category growth/decline trend indicators
- Sector stability metrics and employment type breakdowns

### Key Capabilities
- **1M+ job postings** analyzed (1,048,585 raw records)
- **43 job categories** across all major industries
- **20 months** of temporal data (Oct 2022 - May 2024)
- **AI Forecasting** - 6-month predictions using Facebook Prophet
- **Multi-category filtering** - jobs discoverable by any category
- **Static HTML export** - share insights without any setup
- **Streamlit Cloud ready** - deploy with one click

---

## Technology Stack

**Dashboard**
- Streamlit (web framework)
- Plotly (interactive charts)

**Data Processing**
- Pandas, NumPy (data manipulation)
- PyArrow (Parquet I/O)

**Predictive Analytics**
- Facebook Prophet (time series forecasting, pre-computed)

**Architecture**
- Bronze-Silver-Gold data layers
- Parquet columnar storage (5.5x compression)
- Cached aggregations for sub-second performance

---

## Data Pipeline

### Bronze -> Silver -> Gold Architecture

**Bronze Layer (Raw)**
- Source: SGJobData.csv (273 MB)
- 1,048,585 job postings, 22 fields

**Silver Layer (Cleaned)**
- Removed 10 synthetic test rows (RANDOM_JOB_* with $23M salaries)
- Removed 3,988 completely empty rows (all key fields NaN)
- Parsed 43 job categories from JSON
- Fixed seniority mapping (250K rows corrected from "Unknown" to proper bucket)
- Winsorized salary outliers at p1/p99 (min/max clipped, average recomputed)
- Imputed missing salaries via 3-tier group median strategy
- Standardized text fields (Title Case)
- Created 16 engineered features
- Output: 65.7 MB Parquet (1,044,587 rows, 38 columns)

**Gold Layer (Aggregated)**
- 8 pre-aggregated metric tables (including trends and forecasts)
- Total size: 0.04 MB
- Enables sub-second dashboard loading

### Data Quality

| Metric | Result |
|--------|--------|
| Raw Rows | 1,048,585 |
| Clean Rows | 1,044,587 (99.62% preserved) |
| Rows Removed | 3,998 (10 test + 3,988 empty) |
| Categories | 43 (after removing Unknown) |
| Seniority Unknown | 0% (was 24% before fix) |
| Salary Coverage | 100% (after imputation) |
| Data Quality Score | 9/10 |

---

## Deployment

### Streamlit Cloud
1. Fork/clone this repo
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Deploy with main file: `dashboard/app.py`

### Static HTML
Open `dashboard/singapore_jobs_dashboard.html` in any browser - no Python needed.

---

## Key Insights

From 1M+ job postings analyzed:

- **Top 3 Categories**: Admin/Secretarial, IT, Engineering (~100K each)
- **Avg Market Salary**: ~$3,800/month (weighted by job volume)
- **Salary Range**: $1,000 - $20,000+ (entry to senior management)
- **Multi-Category Jobs**: 37% of postings span multiple sectors
- **Employment Types**: 44% Permanent, 38% Full Time, 13% Contract
- **Seniority Split**: 40% Entry, 45% Mid, 15% Senior

---

## Additional Resources

- **Detailed Report**: See [REPORT.md](REPORT.md) for comprehensive documentation
- **Data Quality Notebook**: See `notebooks/02_data_quality_and_cleaning.ipynb`
- **Data Source**: Singapore MyCareersFuture.sg (Oct 2022 - May 2024)

---

## Author

Developed as part of Singapore Coding and Tech Professionals (SCTP) Data Coaching Module 1 Assignment.

## License

MIT License - feel free to use this project for learning purposes.
