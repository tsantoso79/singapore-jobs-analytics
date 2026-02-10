"""
Talent Acquisition Dashboard
For HR teams and recruiters
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="Talent Acquisition", page_icon="🎯", layout="wide")


@st.cache_data
def load_data():
    """Load Gold layer data"""
    base_dir = Path(__file__).parent.parent.parent
    gold_dir = base_dir / 'data' / 'gold'

    try:
        forecast_file = gold_dir / 'job_forecasts.parquet'

        return {
            'category': pd.read_parquet(gold_dir / 'category_metrics.parquet'),
            'position': pd.read_parquet(gold_dir / 'position_metrics.parquet'),
            'time_series': pd.read_parquet(gold_dir / 'time_series.parquet'),
            'employment': pd.read_parquet(gold_dir / 'employment_metrics.parquet'),
            'salary_dist': pd.read_parquet(gold_dir / 'salary_distribution.parquet'),
            'forecasts': pd.read_parquet(forecast_file) if forecast_file.exists() else pd.DataFrame()
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
    st.title("🎯 Talent Acquisition Intelligence")
    st.markdown("### Identify in-demand roles, competitive salaries, and hiring trends")

    # Load data
    data = load_data()

    # Sidebar filters
    st.sidebar.header("Filters")

    selected_categories = st.sidebar.multiselect(
        "Job Categories",
        options=data['category']['primary_category'].tolist(),
        default=data['category'].nlargest(5, 'job_count')['primary_category'].tolist()
    )

    # Filter data
    if selected_categories:
        filtered_cat = data['category'][data['category']['primary_category'].isin(selected_categories)]
        filtered_ts = data['time_series'][data['time_series']['category'].isin(selected_categories)]
        filtered_salary = data['salary_dist'][data['salary_dist']['primary_category'].isin(selected_categories)]
    else:
        filtered_cat = data['category']
        filtered_ts = data['time_series']
        filtered_salary = data['salary_dist']

    # KPIs
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_roles = filtered_cat['job_count'].sum()
        st.metric("Total Roles", f"{total_roles:,}")

    with col2:
        # Weighted median: weight by job_count so large categories count more
        weighted_sal = (filtered_cat['median_salary'] * filtered_cat['job_count']).sum() / filtered_cat['job_count'].sum()
        st.metric("Avg Market Salary", f"${weighted_sal:,.0f}/mo")

    with col3:
        avg_applications = filtered_cat['total_applications'].sum() / filtered_cat['job_count'].sum()
        st.metric("Avg Applications/Job", f"{avg_applications:.1f}")

    with col4:
        categories_count = len(filtered_cat)
        st.metric("Categories Analyzed", f"{categories_count}")

    # Main visualizations
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top In-Demand Roles")

        top_roles = filtered_cat.nlargest(15, 'job_count')

        fig = px.bar(
            top_roles,
            y='primary_category',
            x='job_count',
            orientation='h',
            color='median_salary',
            color_continuous_scale='Viridis',
            labels={'job_count': 'Number of Postings', 'primary_category': 'Category'},
            text='job_count'
        )
        fig.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Salary Competitiveness")

        salary_comparison = filtered_cat.nlargest(15, 'job_count')

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=salary_comparison['median_salary'],
            y=salary_comparison['primary_category'],
            mode='markers',
            marker=dict(
                size=10 + (salary_comparison['job_count'] - salary_comparison['job_count'].min()) / max(salary_comparison['job_count'].max() - salary_comparison['job_count'].min(), 1) * 40,
                color=salary_comparison['median_salary'],
                colorscale='Blues',
                showscale=True,
                colorbar=dict(title="Salary")
            ),
            text=salary_comparison['primary_category'],
            customdata=salary_comparison[['job_count']],
            hovertemplate='<b>%{text}</b><br>Salary: $%{x:,.0f}<br>Jobs: %{customdata[0]:,}<extra></extra>'
        ))

        fig.update_layout(
            title="Salary vs Demand (bubble size = job count)",
            xaxis_title="Median Salary ($)",
            yaxis_title="",
            height=500,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    # Time series trends
    st.markdown("---")
    st.subheader("📈 Hiring Trends Over Time")

    # Aggregate by month
    ts_monthly = filtered_ts.groupby('year_month')['job_count'].sum().reset_index()
    ts_monthly['year_month'] = pd.to_datetime(ts_monthly['year_month'].astype(str))

    fig = px.area(
        ts_monthly,
        x='year_month',
        y='job_count',
        labels={'year_month': 'Month', 'job_count': 'Job Postings'},
        title="Monthly Posting Volume"
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    # Forecasting section
    if not data['forecasts'].empty:
        st.markdown("---")
        st.subheader("🔮 6-Month Job Posting Forecast (AI Prediction)")

        # Filter forecasts to selected categories
        forecast_data = data['forecasts'].copy()
        if selected_categories:
            forecast_data = forecast_data[forecast_data['category'].isin(selected_categories)]

        if not forecast_data.empty:
            # Combine historical and forecast data
            historical = filtered_ts.copy()
            historical['year_month'] = pd.to_datetime(historical['year_month'].astype(str))

            fig = go.Figure()

            # Add historical data for each category
            for category in forecast_data['category'].unique():
                hist_cat = historical[historical['category'] == category]

                # Historical line
                fig.add_trace(go.Scatter(
                    x=hist_cat['year_month'],
                    y=hist_cat['job_count'],
                    mode='lines',
                    name=f'{category} (Historical)',
                    line=dict(width=2),
                    showlegend=True
                ))

                # Forecast line with confidence interval
                forecast_cat = forecast_data[forecast_data['category'] == category]

                fig.add_trace(go.Scatter(
                    x=forecast_cat['ds'],
                    y=forecast_cat['yhat'],
                    mode='lines',
                    name=f'{category} (Forecast)',
                    line=dict(width=2, dash='dash'),
                    showlegend=True
                ))

                # Confidence interval
                fig.add_trace(go.Scatter(
                    x=forecast_cat['ds'].tolist() + forecast_cat['ds'].tolist()[::-1],
                    y=forecast_cat['yhat_upper'].tolist() + forecast_cat['yhat_lower'].tolist()[::-1],
                    fill='toself',
                    fillcolor='rgba(0,100,80,0.2)',
                    line=dict(color='rgba(255,255,255,0)'),
                    name=f'{category} (Confidence)',
                    showlegend=False
                ))

            fig.update_layout(
                title="Historical Data + 6-Month Forecast (with confidence intervals)",
                xaxis_title="Month",
                yaxis_title="Job Postings",
                height=500,
                hovermode='x unified'
            )

            st.plotly_chart(fig, use_container_width=True)

            # Forecast insights
            st.info("""
            **📊 Forecast Insights:**
            - Predictions generated using Facebook Prophet AI model
            - Shaded areas show confidence intervals (uncertainty range)
            - Use forecasts to plan hiring strategies 3-6 months ahead
            - Forecasts are based on historical patterns and may not account for sudden market changes
            """)
        else:
            st.info("Select categories from the sidebar to see forecasts")

    # Detailed table
    st.markdown("---")
    st.subheader("📊 Detailed Category Breakdown")

    display_df = filtered_cat[[
        'primary_category', 'job_count', 'median_salary', 'mean_salary',
        'total_applications', 'avg_experience_required'
    ]].copy()

    display_df.columns = [
        'Category', 'Job Count', 'Median Salary', 'Mean Salary',
        'Total Applications', 'Avg Experience (years)'
    ]

    display_df['Median Salary'] = display_df['Median Salary'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")
    display_df['Mean Salary'] = display_df['Mean Salary'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")
    display_df['Job Count'] = display_df['Job Count'].apply(lambda x: f"{x:,}" if pd.notna(x) else "0")
    display_df['Total Applications'] = display_df['Total Applications'].apply(lambda x: f"{x:,}" if pd.notna(x) else "0")
    display_df['Avg Experience (years)'] = display_df['Avg Experience (years)'].round(1)

    st.dataframe(display_df, use_container_width=True, height=400)

    # Insights
    st.markdown("---")
    st.subheader("💡 Key Insights")

    col1, col2 = st.columns(2)

    with col1:
        st.info(f"""
        **Most In-Demand Role:**
        {filtered_cat.nlargest(1, 'job_count')['primary_category'].iloc[0]}
        ({filtered_cat.nlargest(1, 'job_count')['job_count'].iloc[0]:,} postings)
        """)

        st.success(f"""
        **Highest Paying Role:**
        {filtered_cat.nlargest(1, 'median_salary')['primary_category'].iloc[0]}
        (${filtered_cat.nlargest(1, 'median_salary')['median_salary'].iloc[0]:,.0f}/month)
        """)

    with col2:
        st.warning(f"""
        **Most Competitive:**
        {filtered_cat.nlargest(1, 'total_applications')['primary_category'].iloc[0]}
        ({filtered_cat.nlargest(1, 'total_applications')['total_applications'].iloc[0]:,} applications)
        """)

        avg_exp = filtered_cat['avg_experience_required'].mean()
        st.info(f"""
        **Average Experience Required:**
        {avg_exp:.1f} years across selected categories
        """)


if __name__ == "__main__":
    main()
