"""
Data Pipeline: Bronze -> Silver -> Gold
Handles cleaning, feature engineering, and aggregation
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class DataPipeline:
    """ETL pipeline for Singapore Jobs data"""

    def __init__(self, data_path):
        self.data_path = Path(data_path)
        self.base_dir = self.data_path.parent
        self.df_raw = None
        self.df_clean = None
        self.df_gold = None

    def load_bronze(self):
        """Load raw data from Bronze layer"""
        print("="*80)
        print("LOADING BRONZE LAYER (Raw Data)")
        print("="*80)

        print(f"\nLoading: {self.data_path}")
        self.df_raw = pd.read_csv(self.data_path, low_memory=False)

        print(f"[OK] Loaded {len(self.df_raw):,} rows x {len(self.df_raw.columns)} columns")
        print(f"Memory: {self.df_raw.memory_usage(deep=True).sum() / (1024**2):.1f} MB")

        return self.df_raw

    def clean_data(self):
        """Transform Bronze -> Silver (cleaned data)"""
        print("\n" + "="*80)
        print("CLEANING DATA (Bronze -> Silver)")
        print("="*80)

        df = self.df_raw.copy()
        original_rows = len(df)

        print(f"\nStarting rows: {original_rows:,}")

        # 0. Remove synthetic/test rows (fake job IDs with RANDOM_JOB prefix)
        if 'metadata_jobPostId' in df.columns:
            test_rows = df['metadata_jobPostId'].str.startswith('RANDOM_JOB', na=False)
            test_count = test_rows.sum()
            if test_count > 0:
                print(f"\n[0] Removing {test_count} synthetic test rows (RANDOM_JOB_* IDs)")
                df = df[~test_rows]

        # 0b. Remove completely empty rows (all key fields are NaN)
        empty_mask = df['title'].isna() & df['postedCompany_name'].isna() & df['metadata_jobPostId'].isna()
        empty_count = empty_mask.sum()
        if empty_count > 0:
            print(f"    Removing {empty_count} completely empty rows")
            df = df[~empty_mask]

        # 1. Drop completely null columns
        print("\n[1] Dropping null columns...")
        null_cols = df.columns[df.isnull().all()].tolist()
        if null_cols:
            print(f"    Dropping: {null_cols}")
            df = df.drop(columns=null_cols)

        # 2. Parse dates
        print("\n[2] Parsing dates...")
        date_cols = ['metadata_expiryDate', 'metadata_newPostingDate', 'metadata_originalPostingDate']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                print(f"    {col}: {df[col].notna().sum():,} valid dates")

        # 3. Parse categories JSON
        print("\n[3] Parsing categories...")
        df['categories_parsed'] = df['categories'].apply(self._parse_json_safe)
        df['num_categories'] = df['categories_parsed'].apply(len)

        # Extract primary category
        df['primary_category'] = df['categories_parsed'].apply(
            lambda x: x[0].get('category', 'Unknown') if x and len(x) > 0 else 'Unknown'
        )

        # Extract ALL categories as list (for filtering)
        df['all_categories_list'] = df['categories_parsed'].apply(
            lambda x: [cat.get('category', 'Unknown') for cat in x] if x else ['Unknown']
        )

        # Create display string
        df['all_categories_str'] = df['all_categories_list'].apply(lambda x: ', '.join(x))

        print(f"    Parsed categories: {df['primary_category'].nunique()} unique")
        print(f"    Multi-category jobs: {(df['num_categories'] > 1).sum():,} ({(df['num_categories'] > 1).mean()*100:.1f}%)")

        # 4. Handle salary logic errors
        print("\n[4] Fixing salary logic errors...")

        # Swap min/max if reversed
        swap_mask = df['salary_minimum'] > df['salary_maximum']
        swap_count = swap_mask.sum()
        if swap_count > 0:
            print(f"    Swapping min/max for {swap_count:,} rows")
            df.loc[swap_mask, ['salary_minimum', 'salary_maximum']] = df.loc[swap_mask, ['salary_maximum', 'salary_minimum']].values

        # Replace zero salaries with NaN for imputation
        for col in ['salary_minimum', 'salary_maximum', 'average_salary']:
            zero_count = (df[col] == 0).sum()
            if zero_count > 0:
                print(f"    Replacing {zero_count:,} zero values in {col} with NaN")
                df.loc[df[col] == 0, col] = np.nan

        # Recalculate average_salary
        df['average_salary'] = (df['salary_minimum'] + df['salary_maximum']) / 2

        # 5. Winsorize salary outliers (only min/max, then recompute average)
        print("\n[5] Handling salary outliers (winsorization)...")
        for col in ['salary_minimum', 'salary_maximum']:
            if df[col].notna().sum() > 0:
                p1 = df[col].quantile(0.01)
                p99 = df[col].quantile(0.99)

                outliers_low = (df[col] < p1).sum()
                outliers_high = (df[col] > p99).sum()

                if outliers_low > 0 or outliers_high > 0:
                    print(f"    {col}: Winsorizing {outliers_low + outliers_high:,} outliers")
                    df[col] = df[col].clip(lower=p1, upper=p99)

        # Recompute average_salary from clipped min/max to maintain consistency
        df['average_salary'] = (df['salary_minimum'] + df['salary_maximum']) / 2
        print("    average_salary: Recomputed from clipped min/max")

        # 6. Standardize text fields
        print("\n[6] Standardizing text fields...")

        # Position levels - Title Case
        if 'positionLevels' in df.columns:
            df['positionLevels'] = df['positionLevels'].str.strip().str.title()
            print(f"    positionLevels: {df['positionLevels'].nunique()} unique values")

        # Employment types - Title Case
        if 'employmentTypes' in df.columns:
            df['employmentTypes'] = df['employmentTypes'].str.strip().str.title()
            print(f"    employmentTypes: {df['employmentTypes'].nunique()} unique values")

        # Job titles - strip whitespace
        if 'title' in df.columns:
            df['title'] = df['title'].str.strip()

        # Company names - strip whitespace
        if 'postedCompany_name' in df.columns:
            df['postedCompany_name'] = df['postedCompany_name'].str.strip()

        # 7. Handle missing values
        print("\n[7] Handling missing values...")

        # Impute missing salaries with median by (category, position level)
        if df['average_salary'].isnull().sum() > 0:
            missing_count = df['average_salary'].isnull().sum()
            print(f"    Imputing {missing_count:,} missing salaries...")

            # Group-based imputation
            df['salary_imputed'] = df.groupby(['primary_category', 'positionLevels'])['average_salary'].transform(
                lambda x: x.fillna(x.median())
            )

            # If still missing, use category median
            df['salary_imputed'] = df.groupby('primary_category')['salary_imputed'].transform(
                lambda x: x.fillna(x.median())
            )

            # If still missing, use global median
            df['salary_imputed'] = df['salary_imputed'].fillna(df['average_salary'].median())

            # Track which were imputed
            df['salary_was_imputed'] = df['average_salary'].isnull()

            # Fill the actual column
            df['average_salary'] = df['salary_imputed']
            df = df.drop(columns=['salary_imputed'])

        # 8. Remove duplicates
        print("\n[8] Removing duplicates...")
        # Exclude list columns from duplicate check
        check_cols = [col for col in df.columns if col not in ['categories_parsed', 'all_categories_list']]
        dup_count = df.duplicated(subset=check_cols).sum()
        if dup_count > 0:
            print(f"    Removing {dup_count:,} exact duplicates")
            df = df.drop_duplicates(subset=check_cols)

        # 9. Create date features
        print("\n[9] Creating date features...")
        if 'metadata_originalPostingDate' in df.columns:
            df['posted_year'] = df['metadata_originalPostingDate'].dt.year
            df['posted_month'] = df['metadata_originalPostingDate'].dt.month
            df['posted_quarter'] = df['metadata_originalPostingDate'].dt.quarter
            df['posted_year_month'] = df['metadata_originalPostingDate'].dt.to_period('M')
            print(f"    Date range: {df['metadata_originalPostingDate'].min().date()} to {df['metadata_originalPostingDate'].max().date()}")

        # 10. Final cleanup
        print(f"\n[10] Final row count: {len(df):,}")
        rows_lost = original_rows - len(df)
        print(f"     Rows removed: {rows_lost:,} ({rows_lost/original_rows*100:.2f}%)")

        self.df_clean = df
        return df

    def engineer_features(self):
        """Add derived features for analysis"""
        print("\n" + "="*80)
        print("FEATURE ENGINEERING")
        print("="*80)

        df = self.df_clean.copy()

        # 1. Seniority mapping
        print("\n[1] Creating seniority levels...")
        seniority_map = {
            'Fresh / Entry Level': 'Entry',
            'Fresh/Entry Level': 'Entry',
            'Junior Executive': 'Entry',
            'Non-Executive': 'Entry',
            'Executive': 'Mid',
            'Senior Executive': 'Mid',
            'Professional': 'Mid',
            'Manager': 'Senior',
            'Middle Management': 'Senior',
            'Senior Management': 'Senior',
        }
        df['seniority_level'] = df['positionLevels'].map(seniority_map).fillna('Unknown')
        print(f"    Distribution: {df['seniority_level'].value_counts().to_dict()}")

        # 2. Salary bands
        print("\n[2] Creating salary bands...")
        df['salary_band'] = pd.cut(
            df['average_salary'],
            bins=[0, 2500, 4000, 6000, 10000, float('inf')],
            labels=['Low (<$2.5K)', 'Medium ($2.5-4K)', 'High ($4-6K)', 'Very High ($6-10K)', 'Premium (>$10K)']
        )
        print(f"    Distribution: {df['salary_band'].value_counts().to_dict()}")

        # 3. Experience bins
        print("\n[3] Creating experience categories...")
        df['experience_category'] = pd.cut(
            df['minimumYearsExperience'],
            bins=[-1, 0, 2, 5, 10, float('inf')],
            labels=['No Experience', 'Entry (0-2yr)', 'Mid (2-5yr)', 'Senior (5-10yr)', 'Expert (10+yr)']
        )

        # 4. Job popularity score
        print("\n[4] Calculating job engagement metrics...")
        if 'metadata_totalNumberOfView' in df.columns and 'metadata_totalNumberJobApplication' in df.columns:
            df['application_rate'] = np.where(
                df['metadata_totalNumberOfView'] > 0,
                df['metadata_totalNumberJobApplication'] / df['metadata_totalNumberOfView'],
                0
            )

            # Engagement score (normalized)
            df['engagement_score'] = (
                df['metadata_totalNumberOfView'] / df['metadata_totalNumberOfView'].max() * 0.6 +
                df['metadata_totalNumberJobApplication'] / df['metadata_totalNumberJobApplication'].max() * 0.4
            ) * 100

        # 5. Multi-category flag
        df['is_multi_category'] = df['num_categories'] > 1

        # 6. Salary competitiveness (percentile within category)
        print("\n[5] Calculating salary competitiveness...")
        df['salary_percentile'] = df.groupby('primary_category')['average_salary'].rank(pct=True) * 100

        df['salary_competitiveness'] = pd.cut(
            df['salary_percentile'],
            bins=[0, 33, 66, 100],
            labels=['Below Market', 'At Market', 'Above Market']
        )

        print(f"    [OK] Added {len([c for c in df.columns if c not in self.df_clean.columns])} new features")

        self.df_clean = df
        return df

    def create_gold_layer(self):
        """Create aggregated Gold layer for dashboard"""
        print("\n" + "="*80)
        print("CREATING GOLD LAYER (Aggregated Metrics)")
        print("="*80)

        df = self.df_clean

        gold_metrics = {}

        # 1. Category-level aggregations
        print("\n[1] Category-level metrics...")
        category_agg = df.groupby('primary_category').agg({
            'title': 'count',
            'average_salary': ['median', 'mean', 'std'],
            'metadata_totalNumberOfView': 'sum',
            'metadata_totalNumberJobApplication': 'sum',
            'minimumYearsExperience': 'mean'
        }).round(2)

        category_agg.columns = ['job_count', 'median_salary', 'mean_salary', 'std_salary',
                                'total_views', 'total_applications', 'avg_experience_required']
        category_agg = category_agg.reset_index()
        category_agg = category_agg.sort_values('job_count', ascending=False)

        print(f"    Created metrics for {len(category_agg)} categories")

        # 2. Position level aggregations
        print("\n[2] Position level metrics...")
        position_agg = df.groupby('positionLevels').agg({
            'title': 'count',
            'average_salary': ['median', 'mean'],
            'minimumYearsExperience': 'mean'
        }).round(2)

        position_agg.columns = ['job_count', 'median_salary', 'mean_salary', 'avg_experience']
        position_agg = position_agg.reset_index()

        # 3. Time series data
        print("\n[3] Time series metrics...")
        if 'posted_year_month' in df.columns:
            time_series = df.groupby(['posted_year_month', 'primary_category']).size().reset_index()
            time_series.columns = ['year_month', 'category', 'job_count']
            time_series['year_month'] = time_series['year_month'].astype(str)
        else:
            time_series = pd.DataFrame()

        # 4. Company aggregations
        print("\n[4] Company metrics...")
        company_agg = df.groupby('postedCompany_name').agg({
            'title': 'count',
            'average_salary': 'mean'
        }).round(2)
        company_agg.columns = ['job_count', 'avg_salary']
        company_agg = company_agg.sort_values('job_count', ascending=False).head(100)
        company_agg = company_agg.reset_index()

        # 5. Employment type distribution
        print("\n[5] Employment type metrics...")
        employment_agg = df.groupby(['employmentTypes', 'primary_category']).size().reset_index()
        employment_agg.columns = ['employment_type', 'category', 'job_count']

        # 6. Salary distributions by category and level
        print("\n[6] Salary distribution metrics...")
        salary_dist = df.groupby(['primary_category', 'positionLevels'])['average_salary'].agg([
            ('count', 'count'),
            ('min', 'min'),
            ('p25', lambda x: x.quantile(0.25)),
            ('median', 'median'),
            ('p75', lambda x: x.quantile(0.75)),
            ('max', 'max')
        ]).round(0).reset_index()

        # Store all metrics
        gold_metrics = {
            'category_metrics': category_agg,
            'position_metrics': position_agg,
            'time_series': time_series,
            'company_metrics': company_agg,
            'employment_metrics': employment_agg,
            'salary_distribution': salary_dist
        }

        self.df_gold = gold_metrics

        print(f"\n[OK] Created {len(gold_metrics)} metric tables")

        return gold_metrics

    def save_silver_layer(self):
        """Save cleaned data to Silver layer"""
        print("\n" + "="*80)
        print("SAVING SILVER LAYER")
        print("="*80)

        silver_dir = self.base_dir / 'data' / 'silver'
        silver_dir.mkdir(parents=True, exist_ok=True)

        output_path = silver_dir / 'cleaned_jobs.parquet'

        self.df_clean.to_parquet(output_path, compression='snappy', index=False)

        file_size = output_path.stat().st_size / (1024**2)
        print(f"\n[OK] Saved to: {output_path}")
        print(f"    Size: {file_size:.1f} MB")
        print(f"    Rows: {len(self.df_clean):,}")
        print(f"    Columns: {len(self.df_clean.columns)}")

        return output_path

    def save_gold_layer(self):
        """Save aggregated metrics to Gold layer"""
        print("\n" + "="*80)
        print("SAVING GOLD LAYER")
        print("="*80)

        gold_dir = self.base_dir / 'data' / 'gold'
        gold_dir.mkdir(parents=True, exist_ok=True)

        total_size = 0

        for metric_name, metric_df in self.df_gold.items():
            output_path = gold_dir / f'{metric_name}.parquet'
            metric_df.to_parquet(output_path, compression='snappy', index=False)

            file_size = output_path.stat().st_size / (1024**2)
            total_size += file_size

            print(f"\n[OK] {metric_name}")
            print(f"    File: {output_path.name}")
            print(f"    Size: {file_size:.2f} MB")
            print(f"    Rows: {len(metric_df):,}")

        print(f"\nTotal Gold layer size: {total_size:.2f} MB")

        return gold_dir

    @staticmethod
    def _parse_json_safe(x):
        """Safely parse JSON string"""
        try:
            return json.loads(x) if pd.notna(x) else []
        except:
            return []

    def run_full_pipeline(self):
        """Execute complete ETL pipeline"""
        print("\n" + "#"*80)
        print("# SINGAPORE JOBS DATA PIPELINE")
        print("# Bronze -> Silver -> Gold")
        print("#"*80)

        # Load Bronze
        self.load_bronze()

        # Clean data (Bronze -> Silver)
        self.clean_data()

        # Engineer features
        self.engineer_features()

        # Create Gold layer
        self.create_gold_layer()

        # Save Silver layer
        self.save_silver_layer()

        # Save Gold layer
        self.save_gold_layer()

        print("\n" + "#"*80)
        print("# PIPELINE COMPLETE")
        print("#"*80)

        print(f"\nSummary:")
        print(f"  Raw data: {len(self.df_raw):,} rows")
        print(f"  Cleaned: {len(self.df_clean):,} rows")
        print(f"  Features: {len(self.df_clean.columns)} columns")
        print(f"  Gold metrics: {len(self.df_gold)} tables")

        return self.df_clean, self.df_gold


if __name__ == '__main__':
    # Run pipeline
    base_dir = Path(__file__).parent.parent
    data_path = base_dir / 'SGJobData.csv'

    pipeline = DataPipeline(data_path)
    df_clean, df_gold = pipeline.run_full_pipeline()

    print("\n[OK] Pipeline execution complete!")
