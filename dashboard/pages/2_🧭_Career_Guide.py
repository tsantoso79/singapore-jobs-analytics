"""
Career Guide Dashboard
For job seekers and career coaches
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="Career Guide", page_icon="🧭", layout="wide")


@st.cache_data
def load_data():
    """Load Gold layer data"""
    base_dir = Path(__file__).parent.parent.parent
    gold_dir = base_dir / 'data' / 'gold'

    try:
        return {
            'category': pd.read_parquet(gold_dir / 'category_metrics.parquet'),
            'position': pd.read_parquet(gold_dir / 'position_metrics.parquet'),
            'salary_dist': pd.read_parquet(gold_dir / 'salary_distribution.parquet'),
            'employment': pd.read_parquet(gold_dir / 'employment_metrics.parquet')
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
    st.title("🧭 Career Guidance Portal")
    st.markdown("### Explore career pathways, salary expectations, and skill requirements")

    # Load data
    data = load_data()

    # Sidebar
    st.sidebar.header("Your Profile")

    position_options = data['position']['positionLevels'].tolist()
    current_level = st.sidebar.selectbox(
        "Current Position Level",
        options=position_options,
        index=min(2, len(position_options) - 1)
    )

    interest_categories = st.sidebar.multiselect(
        "Career Interests",
        options=data['category']['primary_category'].tolist(),
        default=data['category'].nlargest(3, 'median_salary')['primary_category'].tolist()
    )

    # KPIs
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)

    current_level_data = data['position'][data['position']['positionLevels'] == current_level].iloc[0]

    with col1:
        st.metric("Your Level", current_level)

    with col2:
        st.metric("Median Salary", f"${current_level_data['median_salary']:,.0f}/mo")

    with col3:
        available_roles = current_level_data['job_count']
        st.metric("Available Roles", f"{available_roles:,}")

    with col4:
        avg_exp = current_level_data['avg_experience']
        st.metric("Typical Experience", f"{avg_exp:.1f} years")

    # Salary progression
    st.markdown("---")
    st.subheader("💰 Salary Progression by Career Level")

    position_ordered = data['position'].sort_values('median_salary')

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=position_ordered['positionLevels'],
        y=position_ordered['median_salary'],
        mode='lines+markers',
        name='Median Salary',
        line=dict(width=3, color='blue'),
        marker=dict(size=12),
        text=position_ordered['median_salary'].round(0),
        texttemplate='$%{text:,}',
        textposition='top center'
    ))

    fig.update_layout(
        title="Salary Growth Path",
        xaxis_title="Position Level",
        yaxis_title="Median Salary ($)",
        height=400,
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

    # Career opportunities
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🎯 Top Opportunities in Your Interests")

        if interest_categories:
            interest_data = data['category'][data['category']['primary_category'].isin(interest_categories)]
            interest_data = interest_data.sort_values('job_count', ascending=False)

            fig = px.bar(
                interest_data,
                x='job_count',
                y='primary_category',
                orientation='h',
                color='median_salary',
                color_continuous_scale='Greens',
                labels={'job_count': 'Job Openings', 'primary_category': 'Category'},
                text='job_count'
            )
            fig.update_traces(texttemplate='%{text:,}', textposition='outside')
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Select career interests in the sidebar to see opportunities")

    with col2:
        st.subheader("📊 Salary Comparison")

        if interest_categories:
            salary_comp = data['category'][data['category']['primary_category'].isin(interest_categories)]

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=salary_comp['primary_category'],
                y=salary_comp['median_salary'],
                name='Median',
                marker_color='lightblue',
                text=salary_comp['median_salary'].round(0),
                texttemplate='$%{text:,}',
                textposition='outside'
            ))

            fig.update_layout(
                title="Median Salary by Category",
                xaxis_title="",
                yaxis_title="Salary ($)",
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

    # Salary distribution detail
    st.markdown("---")
    st.subheader("💵 Detailed Salary Ranges by Role and Level")

    if interest_categories:
        detailed_salary = data['salary_dist'][data['salary_dist']['primary_category'].isin(interest_categories)]

        # Create heatmap
        pivot_data = detailed_salary.pivot_table(
            values='median',
            index='positionLevels',
            columns='primary_category',
            aggfunc='first'
        )

        fig = px.imshow(
            pivot_data,
            labels=dict(x="Category", y="Position Level", color="Median Salary"),
            x=pivot_data.columns,
            y=pivot_data.index,
            color_continuous_scale='YlOrRd',
            aspect="auto"
        )

        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    # Career transition insights
    st.markdown("---")
    st.subheader("🔄 Career Transition Insights")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Most Accessible Transitions:**")

        # Find categories with similar salary ranges
        if interest_categories and len(interest_categories) > 0:
            current_category = interest_categories[0]
            current_salary = data['category'][data['category']['primary_category'] == current_category]['median_salary'].iloc[0]

            # Find similar paying categories (use copy to avoid mutating cached data)
            category_copy = data['category'].copy()
            category_copy['salary_diff'] = abs(category_copy['median_salary'] - current_salary)
            similar_cats = category_copy.nsmallest(6, 'salary_diff')[1:]  # Exclude current

            for _, row in similar_cats.iterrows():
                st.write(f"• **{row['primary_category']}** - ${row['median_salary']:,.0f}/mo ({row['job_count']:,} jobs)")

    with col2:
        st.markdown("**High Growth Opportunities:**")

        # Categories with high job count and good salary
        growth_cats = data['category'].nlargest(5, 'job_count')

        for _, row in growth_cats.iterrows():
            st.write(f"• **{row['primary_category']}** - ${row['median_salary']:,.0f}/mo ({row['job_count']:,} jobs)")

    # Recommendations
    st.markdown("---")
    st.subheader("💡 Personalized Recommendations")

    col1, col2 = st.columns(2)

    with col1:
        if interest_categories and len(interest_categories) > 0:
            # Filter to user's interests
            interest_data = data['category'][data['category']['primary_category'].isin(interest_categories)]
            if len(interest_data) > 0:
                best_value = interest_data.nlargest(1, 'median_salary').iloc[0]
                current_salary = current_level_data['median_salary']
                uplift_pct = ((best_value['median_salary'] - current_salary) / current_salary * 100)
                st.success(f"""
                **Best Value Career Move (from your interests):**
                
                **{best_value['primary_category']}**
                
                - Median Salary: ${best_value['median_salary']:,.0f}/month
                - Available Roles: {best_value['job_count']:,}
                - Salary Uplift: {'+' if uplift_pct > 0 else ''}{uplift_pct:.1f}% vs your current level
                """)
            else:
                st.warning("Select career interests to see personalized recommendations")
        else:
            st.warning("Select career interests in the sidebar")

    with col2:
        if interest_categories and len(interest_categories) > 0:
            interest_data = data['category'][data['category']['primary_category'].isin(interest_categories)]
            top_demand = interest_data.nlargest(min(3, len(interest_data)), 'job_count')
            if len(top_demand) > 0:
                recommendations = "\n".join([f"{i+1}. **{row['primary_category']}** ({row['job_count']:,} jobs)" for i, (_, row) in enumerate(top_demand.iterrows())])
                st.info(f"""
                **High Demand in Your Interests:**

                {recommendations}
                """)
            else:
                st.info("Select interests to see high demand sectors")
        else:
            top_3 = data['category'].nlargest(3, 'job_count')
            st.info(f"""
            **Overall High Demand Sectors:**
            
            1. {top_3.iloc[0]['primary_category']} ({top_3.iloc[0]['job_count']:,} jobs)
            2. {top_3.iloc[1]['primary_category']} ({top_3.iloc[1]['job_count']:,} jobs)
            3. {top_3.iloc[2]['primary_category']} ({top_3.iloc[2]['job_count']:,} jobs)
            
            *Tip: Select your interests for personalized recommendations*
            """)


if __name__ == "__main__":
    main()
