"""
Singapore Jobs Analytics Dashboard
Main entry point and home page
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Page config
st.set_page_config(
    page_title="Singapore Jobs Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stMetric label {
        color: #31333F !important;
    }
    .stMetric [data-testid="stMetricValue"] {
        color: #0E1117 !important;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_gold_data():
    """Load pre-aggregated Gold layer metrics"""
    base_dir = Path(__file__).parent.parent
    gold_dir = base_dir / 'data' / 'gold'

    # Required metric files
    required_files = {
        'category': 'category_metrics.parquet',
        'position': 'position_metrics.parquet',
        'time_series': 'time_series.parquet',
        'company': 'company_metrics.parquet',
        'employment': 'employment_metrics.parquet',
        'salary_dist': 'salary_distribution.parquet'
    }

    # Check all required files exist
    missing_files = []
    for key, filename in required_files.items():
        if not (gold_dir / filename).exists():
            missing_files.append(filename)

    if missing_files:
        st.error(f"""
        **Data files not found!**

        Missing files in `data/gold/`:
        {chr(10).join(f'- {f}' for f in missing_files)}

        Please run the data pipeline first:
        ```
        python src/data_pipeline.py
        ```
        """)
        st.stop()

    # Load all files
    data = {}
    for key, filename in required_files.items():
        data[key] = pd.read_parquet(gold_dir / filename)

    return data


def main():
    """Main dashboard home page"""

    # Header
    st.markdown('<div class="main-header">📊 Singapore Jobs Analytics Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">1M+ Job Postings | 20+ Months of Data | Real-Time Insights</div>', unsafe_allow_html=True)

    # Load data
    with st.spinner("Loading data..."):
        data = load_gold_data()

    # Executive Summary
    st.markdown("---")
    st.header("Executive Summary")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_jobs = data['category']['job_count'].sum()
        st.metric(
            label="Total Job Postings",
            value=f"{total_jobs:,}"
        )

    with col2:
        total_categories = len(data['category'])
        st.metric(
            label="Job Categories",
            value=f"{total_categories}"
        )

    with col3:
        # Weighted average: weight by job_count so large categories count more
        weighted_sal = (data['category']['median_salary'] * data['category']['job_count']).sum() / data['category']['job_count'].sum()
        st.metric(
            label="Avg Market Salary",
            value=f"${weighted_sal:,.0f}/mo"
        )

    with col4:
        total_companies = len(data['company'])
        st.metric(
            label="Top Companies",
            value=f"{total_companies}+"
        )

    # Visualization sections
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Top 15 Job Categories")

        top_categories = data['category'].nlargest(15, 'job_count')

        fig = px.bar(
            top_categories,
            y='primary_category',
            x='job_count',
            orientation='h',
            title="Job Postings by Category",
            labels={'job_count': 'Number of Jobs', 'primary_category': 'Category'},
            color='median_salary',
            color_continuous_scale='Blues',
            text='job_count'
        )
        fig.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig.update_layout(height=500, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("💰 Salary Distribution by Level")

        position_data = data['position'].sort_values('median_salary', ascending=False)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=position_data['positionLevels'],
            x=position_data['median_salary'],
            orientation='h',
            name='Median Salary',
            marker_color='lightblue',
            text=position_data['median_salary'].round(0),
            texttemplate='$%{text:,}',
            textposition='outside'
        ))

        fig.update_layout(
            title="Median Salary by Position Level",
            xaxis_title="Salary ($)",
            yaxis_title="Position Level",
            height=500,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    # Time series
    st.markdown("---")
    st.subheader("📊 Hiring Trends Over Time")

    # Aggregate time series by month
    ts_agg = data['time_series'].groupby('year_month')['job_count'].sum().reset_index()
    ts_agg['year_month'] = pd.to_datetime(ts_agg['year_month'].astype(str))

    fig = px.line(
        ts_agg,
        x='year_month',
        y='job_count',
        title="Total Job Postings Per Month",
        labels={'year_month': 'Month', 'job_count': 'Number of Jobs'},
        markers=True
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    # Business Case Navigation
    st.markdown("---")
    st.header("🎯 Explore by Business Case")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        ### 🎯 Talent Acquisition

        **For HR Teams & Recruiters**

        - Identify in-demand roles
        - Analyze competitive salaries
        - Track hiring trends
        - Benchmark against market

        [Go to Talent Acquisition →](#)
        """)

    with col2:
        st.markdown("""
        ### 🧭 Career Guide

        **For Job Seekers & Career Coaches**

        - Explore career pathways
        - Salary expectations by role
        - Skills requirements
        - Career transition insights

        [Go to Career Guide →](#)
        """)

    with col3:
        st.markdown("""
        ### 📊 Policy Insights

        **For Policy Analysts & Researchers**

        - Workforce trends analysis
        - Industry growth patterns
        - Skills gap identification
        - Economic indicators

        [Go to Policy Insights →](#)
        """)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem 0;'>
        <p><strong>Data Source:</strong> Singapore Jobs Dataset | <strong>Period:</strong> Apr 2023 - Dec 2024 | <strong>Total Records:</strong> 1,048,585</p>
        <p>Built with Streamlit | Data processed using Bronze-Silver-Gold architecture</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
