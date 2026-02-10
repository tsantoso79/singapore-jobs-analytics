"""
Policy Insights Dashboard
For policy analysts and researchers
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="Policy Insights", page_icon="📊", layout="wide")


@st.cache_data
def load_data():
    """Load Gold layer data"""
    base_dir = Path(__file__).parent.parent.parent
    gold_dir = base_dir / 'data' / 'gold'

    try:
        trends_file = gold_dir / 'category_trends.parquet'

        return {
            'category': pd.read_parquet(gold_dir / 'category_metrics.parquet'),
            'position': pd.read_parquet(gold_dir / 'position_metrics.parquet'),
            'time_series': pd.read_parquet(gold_dir / 'time_series.parquet'),
            'employment': pd.read_parquet(gold_dir / 'employment_metrics.parquet'),
            'company': pd.read_parquet(gold_dir / 'company_metrics.parquet'),
            'trends': pd.read_parquet(trends_file) if trends_file.exists() else pd.DataFrame()
        }
    except FileNotFoundError as e:
        st.error(f"""
        **Data file not found!**

        {str(e)}

        Please run the data pipeline first:
        ```
        python src/data_pipeline.py
        ```
        """)
        st.stop()


def main():
    st.title("📊 Policy & Workforce Insights")
    st.markdown("### Analyze workforce trends, industry growth, and economic indicators")

    # Load data
    data = load_data()

    # Macro indicators
    st.markdown("---")
    st.header("📈 Macro Workforce Indicators")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_postings = data['category']['job_count'].sum()
        st.metric("Total Job Market", f"{total_postings:,}")

    with col2:
        total_sectors = len(data['category'])
        st.metric("Active Sectors", f"{total_sectors}")

    with col3:
        weighted_sal = (data['category']['median_salary'] * data['category']['job_count']).sum() / data['category']['job_count'].sum()
        st.metric("Avg Market Salary", f"${weighted_sal:,.0f}/mo")

    with col4:
        total_employers = len(data['company'])
        st.metric("Active Employers", f"{total_employers}+")

    # Industry distribution
    st.markdown("---")
    st.subheader("🏭 Industry Job Distribution")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Treemap of categories (filter out zero counts)
        treemap_data = data['category'][data['category']['job_count'] > 0].copy()
        
        fig = px.treemap(
            treemap_data,
            path=['primary_category'],
            values='job_count',
            color='median_salary',
            color_continuous_scale='RdYlGn',
            title="Job Market Distribution (size = job count, color = salary)"
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Top industries table
        st.markdown("**Top 10 Industries**")

        top_industries = data['category'].nlargest(10, 'job_count')[['primary_category', 'job_count']]
        top_industries.columns = ['Industry', 'Jobs']
        top_industries['Jobs'] = top_industries['Jobs'].apply(lambda x: f"{x:,}")
        top_industries.index = range(1, len(top_industries) + 1)

        st.dataframe(top_industries, use_container_width=True)

    # Employment types analysis
    st.markdown("---")
    st.subheader("📋 Employment Type Distribution")

    col1, col2 = st.columns(2)

    with col1:
        # Aggregate employment types
        emp_total = data['employment'].groupby('employment_type')['job_count'].sum().reset_index()
        emp_total = emp_total.sort_values('job_count', ascending=False)

        fig = px.pie(
            emp_total,
            names='employment_type',
            values='job_count',
            title="Job Market by Employment Type",
            hole=0.4
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Show trend of top 5 employment types
        top_5_emp = emp_total.head(5)['employment_type'].tolist()

        st.markdown("**Employment Type Trends**")
        st.info(f"""
        **Top Employment Types:**
        {chr(10).join([f"{i+1}. {row['employment_type']}: {row['job_count']:,} jobs" for i, (_, row) in enumerate(emp_total.head(5).iterrows())])}

        Showing distribution across all {len(emp_total)} employment categories in the dataset.
        """)

    # Time series trends
    st.markdown("---")
    st.subheader("📊 Hiring Trends Analysis")

    # Aggregate by month
    ts_monthly = data['time_series'].groupby('year_month')['job_count'].sum().reset_index()
    ts_monthly['year_month'] = pd.to_datetime(ts_monthly['year_month'].astype(str))
    ts_monthly = ts_monthly.sort_values('year_month')

    # Calculate moving average
    ts_monthly['MA_3month'] = ts_monthly['job_count'].rolling(window=3, min_periods=1).mean()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=ts_monthly['year_month'],
        y=ts_monthly['job_count'],
        mode='lines',
        name='Actual',
        line=dict(color='lightblue', width=1)
    ))

    fig.add_trace(go.Scatter(
        x=ts_monthly['year_month'],
        y=ts_monthly['MA_3month'],
        mode='lines',
        name='3-Month Moving Average',
        line=dict(color='blue', width=3)
    ))

    fig.update_layout(
        title="Monthly Job Postings with Trend",
        xaxis_title="Month",
        yaxis_title="Number of Jobs",
        height=400,
        hovermode='x unified'
    )

    st.plotly_chart(fig, use_container_width=True)

    # HR Budget Spending Analysis
    st.markdown("---")
    st.subheader("💰 HR Budget Spending by Industry")

    # Calculate monthly budget: job_count × median_salary
    # Merge time series with category metrics to get salary data
    ts_budget = data['time_series'].merge(
        data['category'][['primary_category', 'median_salary']],
        left_on='category',
        right_on='primary_category',
        how='left'
    )

    # Calculate total salary budget per month per category
    ts_budget['monthly_budget'] = ts_budget['job_count'] * ts_budget['median_salary']
    ts_budget['year_month'] = pd.to_datetime(ts_budget['year_month'].astype(str))
    ts_budget = ts_budget.sort_values('year_month')

    # Get top 10 categories by total budget (sorted for consistent coloring)
    top_budget_cats = ts_budget.groupby('category')['monthly_budget'].sum().nlargest(10).sort_values(ascending=False).index.tolist()
    ts_budget_filtered = ts_budget[ts_budget['category'].isin(top_budget_cats)]

    # Define consistent color mapping
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
              '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    color_map = {cat: colors[i % len(colors)] for i, cat in enumerate(top_budget_cats)}

    # Create line chart (clearer than stacked area for comparing individual values)
    fig = px.line(
        ts_budget_filtered,
        x='year_month',
        y='monthly_budget',
        color='category',
        color_discrete_map=color_map,
        title="Monthly HR Budget Spending by Industry (Top 10 - Each Line Shows Actual Budget)",
        labels={
            'year_month': 'Month',
            'monthly_budget': 'Total Salary Budget ($)',
            'category': 'Industry'
        },
        markers=True
    )

    fig.update_layout(
        height=500,
        hovermode='closest',  # Changed from 'x unified' for better tooltip display
        yaxis_tickformat='$,.0f',
        hoverlabel=dict(
            bgcolor="#2d2d2d",
            font_size=13,
            font_color="white",
            font_family="monospace",
            bordercolor="#555"
        )
    )

    # Update hover template to show clear values
    fig.update_traces(
        hovertemplate='<b>%{fullData.name}</b><br>Budget: $%{y:,.0f}<extra></extra>'
    )

    st.plotly_chart(fig, use_container_width=True)

    # Budget insights
    col1, col2 = st.columns(2)

    with col1:
        total_budget = ts_budget['monthly_budget'].sum()
        avg_monthly = ts_budget.groupby('year_month')['monthly_budget'].sum().mean()
        st.metric(
            "Total Advertised Salary Budget",
            f"${total_budget/1e9:.2f}B",
            help="Sum of all advertised salaries across all months"
        )

    with col2:
        st.metric(
            "Average Monthly Budget",
            f"${avg_monthly/1e6:.1f}M",
            help="Average total salary budget per month"
        )

    # Skills gap analysis (proxy: experience requirements)
    st.markdown("---")
    st.subheader("🎓 Workforce Skills Analysis")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Experience Requirements by Industry**")

        exp_req = data['category'].nlargest(15, 'job_count')[['primary_category', 'avg_experience_required']]
        exp_req = exp_req.sort_values('avg_experience_required', ascending=False)

        fig = px.bar(
            exp_req,
            x='avg_experience_required',
            y='primary_category',
            orientation='h',
            title="Average Experience Required (years)",
            labels={'avg_experience_required': 'Years', 'primary_category': 'Category'},
            text='avg_experience_required'
        )
        fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig.update_layout(height=500, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Position Level Distribution**")

        position_dist = data['position'].sort_values('job_count', ascending=False)

        fig = px.bar(
            position_dist,
            x='positionLevels',
            y='job_count',
            title="Jobs by Seniority Level",
            labels={'positionLevels': 'Level', 'job_count': 'Number of Jobs'},
            text='job_count',
            color='median_salary',
            color_continuous_scale='Viridis'
        )
        fig.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

    # Sector growth indicators
    st.markdown("---")
    st.subheader("📈 Sector Growth Indicators")

    # Calculate growth trends from time series
    ts_by_cat = data['time_series'].groupby('category')['job_count'].agg(['sum', 'mean', 'std']).reset_index()
    ts_by_cat.columns = ['category', 'total_jobs', 'avg_monthly', 'volatility']
    ts_by_cat = ts_by_cat.sort_values('total_jobs', ascending=False).head(15)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**High Volume Sectors**")

        fig = px.bar(
            ts_by_cat.head(10),
            x='total_jobs',
            y='category',
            orientation='h',
            title="Total Postings Over Period",
            labels={'total_jobs': 'Total Jobs', 'category': 'Sector'},
            text='total_jobs'
        )
        fig.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Market Stability**")

        fig = px.scatter(
            ts_by_cat,
            x='avg_monthly',
            y='volatility',
            size='total_jobs',
            color='category',
            title="Sector Stability (lower volatility = more stable)",
            labels={'avg_monthly': 'Avg Monthly Jobs', 'volatility': 'Volatility (Std Dev)'},
            hover_data=['category']
        )
        fig.update_layout(
            height=400,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=1.01,
                font=dict(size=8)
            )
        )
        st.plotly_chart(fig, use_container_width=True)

    # Policy recommendations
    st.markdown("---")
    st.subheader("💡 Policy Implications")

    # Compute actual values from data
    top_3_sectors = data['category'].nlargest(3, 'job_count')
    avg_exp = data['category']['avg_experience_required'].mean()
    total_jobs = data['category']['job_count'].sum()
    num_sectors = len(data['category'])
    market_median = data['category']['median_salary'].median()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info(f"""
        **Workforce Development Priority:**

        Top 3 high-demand sectors require focused training:
        - {top_3_sectors.iloc[0]['primary_category']} ({top_3_sectors.iloc[0]['job_count']:,.0f} jobs)
        - {top_3_sectors.iloc[1]['primary_category']} ({top_3_sectors.iloc[1]['job_count']:,.0f} jobs)
        - {top_3_sectors.iloc[2]['primary_category']} ({top_3_sectors.iloc[2]['job_count']:,.0f} jobs)
        """)

    with col2:
        st.warning(f"""
        **Skills Gap Alert:**

        Average experience required: {avg_exp:.1f} years
        - Entry-level shortage in tech sectors
        - Mid-career opportunities abundant
        - Senior positions highly competitive
        """)

    with col3:
        st.success(f"""
        **Economic Indicators:**

        - Total job postings: {total_jobs:,.0f}
        - Employment diversity: {num_sectors} active sectors
        - Median market salary: ${market_median:,.0f}/mo
        - Strong demand across all levels
        """)

    # Detailed metrics table
    st.markdown("---")
    st.subheader("📋 Comprehensive Sector Metrics with Trends")

    detailed_metrics = data['category'][[
        'primary_category', 'job_count', 'median_salary', 'mean_salary',
        'total_views', 'total_applications', 'avg_experience_required'
    ]].copy()

    # Merge with trends data if available
    if not data['trends'].empty:
        detailed_metrics = detailed_metrics.merge(
            data['trends'][['primary_category', 'trend_pct_change', 'trend_icon']],
            on='primary_category',
            how='left'
        )

    detailed_metrics.columns = [
        'Sector', 'Jobs', 'Median Salary', 'Mean Salary',
        'Total Views', 'Applications', 'Avg Experience'
    ] + (['Trend %', 'Trend'] if not data['trends'].empty else [])

    detailed_metrics = detailed_metrics.sort_values('Jobs', ascending=False)

    # Format for display (with NaN guards)
    detailed_metrics['Jobs'] = detailed_metrics['Jobs'].apply(lambda x: f"{x:,}" if pd.notna(x) else "0")
    detailed_metrics['Median Salary'] = detailed_metrics['Median Salary'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")
    detailed_metrics['Mean Salary'] = detailed_metrics['Mean Salary'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")
    detailed_metrics['Total Views'] = detailed_metrics['Total Views'].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "0")
    detailed_metrics['Applications'] = detailed_metrics['Applications'].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "0")
    detailed_metrics['Avg Experience'] = detailed_metrics['Avg Experience'].round(1)

    if not data['trends'].empty and 'Trend %' in detailed_metrics.columns:
        detailed_metrics['Trend %'] = detailed_metrics['Trend %'].apply(
            lambda x: f"+{x:.1f}%" if pd.notna(x) and x > 0 else f"{x:.1f}%" if pd.notna(x) else "N/A"
        )

    st.dataframe(detailed_metrics, use_container_width=True, height=400)


if __name__ == "__main__":
    main()
