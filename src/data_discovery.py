"""
Data Discovery & Validation Script
Runs critical validations and generates discovery report
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime

def load_data(file_path):
    """Load CSV with optimized dtypes"""
    print(f"Loading data from: {file_path}")
    print(f"File size: {file_path.stat().st_size / (1024**2):.1f} MB\n")

    # Optimized dtypes
    dtype_spec = {
        'categories': 'object',
        'company': 'category',
        'employmentType': 'category',
        'jobTitle': 'object',
        'positionLevel': 'category'
    }

    df = pd.read_csv(file_path, dtype=dtype_spec, low_memory=False)
    print(f"[OK] Loaded {len(df):,} rows x {len(df.columns)} columns")
    print(f"Memory usage: {df.memory_usage(deep=True).sum() / (1024**2):.1f} MB\n")

    return df

def validate_temporal_coverage(df):
    """CRITICAL VALIDATION #1: Check if we have enough data for forecasting"""
    print("="*80)
    print("VALIDATION #1: TEMPORAL COVERAGE")
    print("="*80 + "\n")

    # Find date columns
    date_cols = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
    print(f"Date columns found: {date_cols}\n")

    forecasting_feasible = 'unknown'

    for col in date_cols:
        try:
            date_series = pd.to_datetime(df[col], errors='coerce')
            non_null = date_series.notna().sum()

            if non_null > 0:
                date_min = date_series.min()
                date_max = date_series.max()
                time_span_days = (date_max - date_min).days
                time_span_months = time_span_days / 30

                print(f"Column: {col}")
                print(f"  Range: {date_min.date()} to {date_max.date()}")
                print(f"  Span: {time_span_days} days ({time_span_months:.1f} months)")
                print(f"  Coverage: {non_null:,} records ({non_null/len(df)*100:.1f}%)\n")

                if time_span_months < 6:
                    print("  [WARNING] DECISION: INSUFFICIENT FOR FORECASTING")
                    print("  -> Use descriptive statistics and trend analysis only\n")
                    forecasting_feasible = False
                elif time_span_months < 12:
                    print("  [WARNING] DECISION: LIMITED DATA")
                    print("  -> Use basic trend decomposition, avoid Prophet\n")
                    forecasting_feasible = 'limited'
                else:
                    print("  [OK] DECISION: SUFFICIENT FOR FORECASTING")
                    print("  -> Prophet/ARIMA models feasible\n")
                    forecasting_feasible = True

                return forecasting_feasible, {
                    'date_column': col,
                    'date_min': str(date_min),
                    'date_max': str(date_max),
                    'time_span_months': time_span_months,
                    'coverage_pct': non_null/len(df)*100
                }
        except Exception as e:
            print(f"  Error parsing {col}: {e}\n")

    print("[WARNING] No valid date columns found\n")
    return forecasting_feasible, None

def validate_file_size(df, original_path):
    """CRITICAL VALIDATION #2: Check if processed data fits GitHub limits"""
    print("="*80)
    print("VALIDATION #2: FILE SIZE FOR DEPLOYMENT")
    print("="*80 + "\n")

    # Test Parquet compression
    test_path = Path('../data/silver/test_size.parquet')
    test_path.parent.mkdir(parents=True, exist_ok=True)

    print("Testing Parquet compression...")
    df.to_parquet(test_path, compression='snappy', index=False)

    parquet_size_mb = test_path.stat().st_size / (1024**2)
    original_size_mb = original_path.stat().st_size / (1024**2)
    compression_ratio = original_size_mb / parquet_size_mb

    print(f"Original CSV: {original_size_mb:.1f} MB")
    print(f"Parquet (snappy): {parquet_size_mb:.1f} MB")
    print(f"Compression: {compression_ratio:.1f}x\n")

    github_compatible = parquet_size_mb <= 50

    if github_compatible:
        print(f"[OK] DECISION: GITHUB COMPATIBLE ({parquet_size_mb:.1f}MB)")
        print("-> Can include Silver layer in repository\n")
    else:
        print(f"[WARNING] DECISION: TOO LARGE FOR GITHUB ({parquet_size_mb:.1f}MB)")
        print("-> Dashboard loads from Gold layer only (pre-aggregated)")
        print("-> Estimated Gold layer: ~5-10MB\n")

    test_path.unlink()  # Clean up

    return github_compatible, {
        'original_size_mb': original_size_mb,
        'parquet_size_mb': parquet_size_mb,
        'compression_ratio': compression_ratio,
        'deployment_strategy': 'Silver layer' if github_compatible else 'Gold layer only'
    }

def validate_category_structure(df):
    """CRITICAL VALIDATION #3: Parse and analyze category JSON structure"""
    print("="*80)
    print("VALIDATION #3: CATEGORY STRUCTURE")
    print("="*80 + "\n")

    if 'categories' not in df.columns:
        print("[WARNING] No 'categories' column found\n")
        return None

    print("Sample categories:")
    print(df['categories'].head(3).tolist())
    print()

    # Safe JSON parsing
    def safe_parse(x):
        try:
            return json.loads(x) if pd.notna(x) else []
        except:
            return []

    df['categories_parsed'] = df['categories'].apply(safe_parse)
    df['num_categories'] = df['categories_parsed'].apply(len)

    print("Category multiplicity:")
    print(df['num_categories'].value_counts().sort_index())
    print(f"\nMulti-category jobs: {(df['num_categories'] > 1).sum():,} ({(df['num_categories'] > 1).mean()*100:.1f}%)")
    print(f"Avg categories/job: {df['num_categories'].mean():.2f}\n")

    # Extract primary category
    def get_primary(cat_list):
        if cat_list and len(cat_list) > 0:
            return cat_list[0].get('category', 'Unknown')
        return 'Unknown'

    df['primary_category'] = df['categories_parsed'].apply(get_primary)

    print("Top 15 primary categories:")
    print(df['primary_category'].value_counts().head(15))
    print(f"\nTotal unique categories: {df['primary_category'].nunique()}\n")

    print("[OK] DECISION: USE PRIMARY CATEGORY")
    print("-> Avoids double-counting multi-category jobs")
    print(f"-> Working with {df['primary_category'].nunique()} categories\n")

    return {
        'total_unique': df['primary_category'].nunique(),
        'multi_category_pct': (df['num_categories'] > 1).mean() * 100,
        'top_categories': df['primary_category'].value_counts().head(10).to_dict()
    }

def generate_profile(df):
    """Generate statistical profile"""
    print("="*80)
    print("STATISTICAL PROFILE")
    print("="*80 + "\n")

    # Basic stats
    print(f"Total rows: {len(df):,}")
    print(f"Total columns: {len(df.columns)}")
    print(f"Memory usage: {df.memory_usage(deep=True).sum() / (1024**2):.1f} MB\n")

    # Missing values
    print("Missing Values:")
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    missing_df = pd.DataFrame({
        'Missing': missing[missing > 0],
        'Percent': missing_pct[missing > 0]
    }).sort_values('Missing', ascending=False)

    if len(missing_df) > 0:
        print(missing_df)
    else:
        print("No missing values")
    print()

    # Salary analysis
    salary_cols = [col for col in df.columns if 'salary' in col.lower()]
    if salary_cols:
        print("Salary Statistics:")
        for col in salary_cols:
            if df[col].dtype in [np.number, 'int64', 'float64']:
                print(f"\n{col}:")
                print(f"  Count: {df[col].notna().sum():,} ({df[col].notna().sum()/len(df)*100:.1f}%)")
                print(f"  Range: ${df[col].min():,.0f} - ${df[col].max():,.0f}")
                print(f"  Median: ${df[col].median():,.0f}")
                print(f"  Mean: ${df[col].mean():,.0f}")
        print()

    # Position levels
    if 'positionLevel' in df.columns:
        print("Position Level Distribution:")
        print(df['positionLevel'].value_counts())
        print()

        if salary_cols:
            print(f"Median Salary by Position Level:")
            print(df.groupby('positionLevel')[salary_cols[0]].median().sort_values(ascending=False))
            print()

    # Employment types
    if 'employmentType' in df.columns:
        print("Employment Type Distribution:")
        print(df['employmentType'].value_counts())
        print()

    # Top companies
    if 'company' in df.columns:
        print("Top 15 Companies by Postings:")
        print(df['company'].value_counts().head(15))
        print()

def main():
    """Run full discovery pipeline"""
    # Setup paths
    base_dir = Path(__file__).parent.parent
    data_path = base_dir / 'SGJobData.csv'

    if not data_path.exists():
        print(f"[ERROR] Data file not found: {data_path}")
        return

    # Load data
    df = load_data(data_path)

    # Run critical validations
    forecasting_result, temporal_info = validate_temporal_coverage(df)
    github_compatible, size_info = validate_file_size(df, data_path)
    category_info = validate_category_structure(df)

    # Generate profile
    generate_profile(df)

    # Compile validation report
    report = {
        'timestamp': datetime.now().isoformat(),
        'dataset_info': {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'columns': df.columns.tolist(),
            'memory_mb': df.memory_usage(deep=True).sum() / (1024**2)
        },
        'temporal_coverage': {
            'forecasting_feasible': forecasting_result,
            'details': temporal_info
        },
        'file_size_check': {
            'github_compatible': github_compatible,
            'details': size_info
        },
        'category_structure': category_info,
        'data_quality_summary': {
            'missing_values': df.isnull().sum().to_dict(),
            'total_missing_pct': (df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100)
        }
    }

    # Save report
    report_path = base_dir / 'data' / 'silver' / 'validation_report.json'
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    print("="*80)
    print("VALIDATION COMPLETE")
    print("="*80)
    print(f"\n[OK] Report saved to: {report_path}")
    print(f"\nKey Decisions:")
    print(f"  • Forecasting: {forecasting_result}")
    print(f"  • GitHub compatible: {github_compatible}")
    print(f"  • Deployment: {size_info['deployment_strategy']}")
    print(f"  • Categories: {category_info['total_unique'] if category_info else 'N/A'}")

if __name__ == '__main__':
    main()
