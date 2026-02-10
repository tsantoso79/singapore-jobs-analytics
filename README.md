# 📊 Singapore Jobs Analytics Dashboard

**1M+ Job Postings | 3 Business Cases | Interactive Analytics**

A comprehensive data analytics dashboard analyzing Singapore's job market across 20+ months (Apr 2023 - Dec 2024). Built to serve talent acquisition teams, career coaches, and policy analysts with real-time insights.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.29.0-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- pip package manager

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd "Assignment 1"
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

---

## 📂 Project Structure

```
Assignment 1/
├── data/
│   └── gold/                          # Pre-aggregated metrics (0.04 MB)
│       ├── category_metrics.parquet
│       ├── position_metrics.parquet
│       ├── time_series.parquet
│       ├── company_metrics.parquet
│       ├── employment_metrics.parquet
│       └── salary_distribution.parquet
├── dashboard/
│   ├── app.py                         # Main dashboard (home page)
│   └── pages/
│       ├── 1_🎯_Talent_Acquisition.py # HR & Recruiter insights
│       ├── 2_🧭_Career_Guide.py       # Job seeker guidance
│       └── 3_📊_Policy_Insights.py    # Workforce analytics
├── src/
│   ├── data_pipeline.py               # ETL pipeline (Bronze → Silver → Gold)
│   ├── quality_checks.py              # Data quality validation
│   └── data_discovery.py              # Initial data profiling
├── requirements.txt                   # Python dependencies
├── README.md                          # This file
├── REPORT.md                          # Detailed project report
└── SGJobData.csv                      # Raw data (not in repo - too large)
```

---

## 🎯 Features

### Three Business Cases Served

**1. Talent Acquisition Dashboard** 🎯
- Identify top in-demand roles and competitive salary ranges
- Track hiring trends over time
- Analyze application competition by category
- Filter by job categories with interactive visualizations

**2. Career Guide Dashboard** 🧭
- Personalized salary progression paths
- Career transition recommendations
- Compare opportunities across interests
- Salary heatmaps by category and seniority

**3. Policy Insights Dashboard** 📊
- Workforce trend analysis with moving averages
- Industry distribution treemaps
- Employment type breakdowns
- Skills gap analysis and sector stability metrics

### Key Capabilities
✅ **1M+ job postings** analyzed (1,048,585 records)
✅ **44 job categories** across all major industries
✅ **20.6 months** of temporal data (Apr 2023 - Dec 2024)
✅ **Multi-category filtering** - jobs discoverable by any category
✅ **Real-time interactivity** - sub-second filter updates
✅ **Pre-aggregated metrics** - blazing fast performance

---

## 🛠️ Technology Stack

**Core**
- Python 3.10+
- Pandas 2.1.4 (data manipulation)
- NumPy 1.26.3 (numerical operations)

**Visualization & Dashboard**
- Streamlit 1.29.0 (web framework)
- Plotly 5.18.0 (interactive charts)

**Data Processing**
- PyArrow 14.0.2 (Parquet I/O)
- Scikit-learn 1.3.2 (outlier detection)

**Architecture**
- Bronze-Silver-Gold data layers
- Parquet columnar storage (5.5x compression)
- Cached aggregations for performance

---

## 📊 Data Pipeline

### Bronze → Silver → Gold Architecture

**Bronze Layer (Raw)**
- Source: SGJobData.csv (273 MB)
- 1,048,585 job postings, 22 fields

**Silver Layer (Cleaned)**
- Parsed 44 job categories from JSON
- Imputed 3,988 missing salaries using group medians
- Winsorized 19,862 outliers at 1st/99th percentiles
- Standardized text fields (Title Case)
- Created 17 engineered features
- Output: 65.7 MB Parquet (1,044,598 rows, 39 columns)

**Gold Layer (Aggregated)**
- 6 pre-aggregated metric tables
- Total size: 0.04 MB
- Enables sub-second dashboard loading

### Data Quality

| Metric | Result |
|--------|--------|
| Missing Data | 0.38% (handled via imputation) |
| Temporal Coverage | 20.6 months (sufficient) |
| Salary Coverage | 100% (after imputation) |
| Outliers Handled | 19,862 winsorized |
| Duplicates | 0 (verified clean) |

---

## 🔧 Usage Examples

### Running the Pipeline
```bash
# Full ETL pipeline
python src/data_pipeline.py

# Data quality checks only
python src/quality_checks.py

# Initial data discovery
python src/data_discovery.py
```

### Launching the Dashboard
```bash
# Default (opens browser automatically)
streamlit run dashboard/app.py

# Headless mode (server only)
streamlit run dashboard/app.py --server.headless true

# Custom port
streamlit run dashboard/app.py --server.port 8502
```

---

## 📈 Key Insights

From 1M+ job postings analyzed:

- **Top 3 Categories**: Admin/Secretarial (103K), IT (100K), Engineering (100K)
- **Median Salary**: $3,800/month across all sectors
- **Salary Range**: $1,000 - $20,000+ (entry to senior management)
- **Multi-Category Jobs**: 37% of postings span multiple sectors
- **Employment Types**: 58% Permanent, 37% Full Time, 13% Contract
- **Experience Required**: Average 2.5 years across all postings

---

## 🤝 Contributing

This is an academic project for a data coaching assignment. For questions or suggestions, please open an issue.

---

## 📝 License

MIT License - feel free to use this project for learning purposes.

---

## 👤 Author

Developed as part of Singapore Coding and Tech Professionals (SCTP) Data Coaching Module 1 Assignment.

---

## 📚 Additional Resources

- **Detailed Report**: See [REPORT.md](REPORT.md) for comprehensive documentation
- **Data Source**: Singapore Jobs Dataset (1M+ postings, Apr 2023 - Dec 2024)
- **Presentation**: 10-minute walkthrough covering business case, process, dashboard, and learnings

---

# Assignment Requirements

## Module 1 Assignment Project – Singapore Jobs Analytics

Design a simple data product (dashboard or web app) using a real-world CSV of Singapore job postings (~1M+ rows). Your goal is to solve a clear business problem for a specific user group using insights from the data.

---

## 1. Business Case (2–3 bullets)

Briefly describe:

- Business scenario (e.g. talent acquisition, policy analyst, career coach).
- **Objective**: What decision/problem are you helping to address?
- Target users and value: How will this dashboard/app help them?

> Example: “Help a talent acquisition team identify which roles and skills are most in demand so they can prioritise hiring and sourcing.”

---

## 2. Data Handling & Process (5–8 bullets)

Summarise your end-to-end process:

- Tools used (e.g. Python + Pandas / DuckDB / SQL).
- How you loaded the CSV (~1M+ rows).
- Key cleaning steps (missing values, standardising categories, parsing dates, handling salary formats).
- Important feature engineering (e.g. seniority, salary bands, demand metrics, skill tags).
- EDA highlights: key patterns or anomalies you discovered that shaped your dashboard design.

You do not need to show all code, but the logic and key decisions should be clear.

---

## 3. Dashboard / App (6–10 bullets)

Describe and demonstrate your solution:

- Type of solution: dashboard (e.g. Streamlit, Power BI, Tableau) or simple web app.
- Main views:
  - Overview metrics (e.g. total postings, top roles/industries, salary ranges).
  - Drill-down view (by role, industry, location, skills, etc.).
  - Time trend view (e.g. postings over time, salary trends).
- Interactivity: filters, sorting, drill-downs, tooltips where relevant.
- Design choices: layout, chart types, colour scheme, readability.
- How each view directly supports your business objective and target users.

Include 2–4 key screenshots in your written submission (or show live in the presentation).

---

## 4. Presentation (10 mins per team)

Suggested flow:

1. **Business case & objective** (2–3 mins)  
   - Scenario, users, objective, success criteria.
2. **Process & data handling** (3–4 mins)  
   - How you cleaned, transformed, and explored the data.
3. **Dashboard / app walkthrough** (3–4 mins)  
   - Main views, interactions, and how they answer the business question.
4. **Challenges & learnings** (1–2 mins)  
   - Technical/analytical challenges, what you learned, and possible next steps.

---

## 5. Deliverables

- Brief written report (Markdown/PDF) following Sections 1–4 above.
- Working dashboard / app (deployed link or clear run instructions).
- Code repo with:
  - Data handling notebook(s) / scripts,
  - Dashboard/app code,
  - README with setup steps.

Focus on a **coherent story** from business question → data process → dashboard → insights, rather than advanced techniques.
