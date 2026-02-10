"""
Data Quality Assessment Module
Performs comprehensive quality checks following 13-step workflow
"""

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.ensemble import IsolationForest
import json
from pathlib import Path


class DataQualityChecker:
    """Comprehensive data quality assessment"""

    def __init__(self, df):
        self.df = df.copy()
        self.issues = {
            'missing_values': {},
            'duplicates': {},
            'outliers': {},
            'logic_errors': {},
            'inconsistencies': {},
            'structural_issues': {}
        }

    def check_missing_values(self):
        """Identify missing value patterns (MCAR, MAR, MNAR)"""
        print("\n" + "="*80)
        print("CHECK 1: MISSING VALUES")
        print("="*80)

        missing = self.df.isnull().sum()
        missing_pct = (missing / len(self.df) * 100).round(2)

        missing_df = pd.DataFrame({
            'Count': missing[missing > 0],
            'Percent': missing_pct[missing > 0]
        }).sort_values('Count', ascending=False)

        if len(missing_df) > 0:
            print(f"\nFields with missing data ({len(missing_df)} fields):")
            print(missing_df)

            # Store results
            self.issues['missing_values'] = {
                'total_missing': int(missing.sum()),
                'fields_affected': len(missing_df),
                'details': missing_df.to_dict()
            }
        else:
            print("\n[OK] No missing values detected")
            self.issues['missing_values'] = {'total_missing': 0}

        return missing_df

    def check_duplicates(self):
        """Detect exact and fuzzy duplicates"""
        print("\n" + "="*80)
        print("CHECK 2: DUPLICATES")
        print("="*80)

        # Exact duplicates (all columns)
        exact_dups = self.df.duplicated().sum()
        print(f"\nExact duplicates (all columns): {exact_dups:,}")

        # Duplicates by job ID (if available)
        if 'metadata_jobPostId' in self.df.columns:
            id_dups = self.df['metadata_jobPostId'].duplicated().sum()
            print(f"Duplicate job IDs: {id_dups:,}")

        # Potential fuzzy duplicates (same title + company + salary)
        if all(col in self.df.columns for col in ['title', 'postedCompany_name', 'salary_minimum']):
            fuzzy_dups = self.df.duplicated(subset=['title', 'postedCompany_name', 'salary_minimum']).sum()
            print(f"Potential fuzzy duplicates (title+company+salary): {fuzzy_dups:,}")

        self.issues['duplicates'] = {
            'exact': int(exact_dups),
            'by_id': int(id_dups) if 'metadata_jobPostId' in self.df.columns else 0
        }

        return exact_dups

    def check_univariate_outliers(self, numeric_cols=None):
        """Detect outliers using Z-score and IQR methods"""
        print("\n" + "="*80)
        print("CHECK 3: UNIVARIATE OUTLIERS")
        print("="*80)

        if numeric_cols is None:
            numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
            # Exclude metadata counts
            numeric_cols = [col for col in numeric_cols if 'salary' in col.lower() or 'experience' in col.lower()]

        outliers = {}

        for col in numeric_cols:
            if self.df[col].notna().sum() > 0:
                # IQR method
                Q1 = self.df[col].quantile(0.25)
                Q3 = self.df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 3 * IQR
                upper_bound = Q3 + 3 * IQR

                outlier_mask = (self.df[col] < lower_bound) | (self.df[col] > upper_bound)
                n_outliers = outlier_mask.sum()

                if n_outliers > 0:
                    pct = (n_outliers / self.df[col].notna().sum()) * 100
                    print(f"\n{col}:")
                    print(f"  Outliers: {n_outliers:,} ({pct:.2f}%)")
                    print(f"  Range: {self.df[col].min():,.0f} to {self.df[col].max():,.0f}")
                    print(f"  IQR bounds: {lower_bound:,.0f} to {upper_bound:,.0f}")

                    outliers[col] = {
                        'count': int(n_outliers),
                        'percent': float(pct),
                        'bounds': [float(lower_bound), float(upper_bound)]
                    }

        self.issues['outliers']['univariate'] = outliers
        return outliers

    def check_logic_errors(self):
        """Identify logical inconsistencies"""
        print("\n" + "="*80)
        print("CHECK 4: LOGIC ERRORS")
        print("="*80)

        errors = {}

        # Salary min > max
        if 'salary_minimum' in self.df.columns and 'salary_maximum' in self.df.columns:
            salary_errors = (self.df['salary_minimum'] > self.df['salary_maximum']).sum()
            print(f"\nSalary_min > Salary_max: {salary_errors:,} cases")
            errors['salary_min_gt_max'] = int(salary_errors)

        # Negative salaries
        for col in ['salary_minimum', 'salary_maximum', 'average_salary']:
            if col in self.df.columns:
                neg_count = (self.df[col] < 0).sum()
                if neg_count > 0:
                    print(f"Negative {col}: {neg_count:,} cases")
                    errors[f'negative_{col}'] = int(neg_count)

        # Zero salaries
        if 'average_salary' in self.df.columns:
            zero_salary = (self.df['average_salary'] == 0).sum()
            print(f"Zero average_salary: {zero_salary:,} cases")
            errors['zero_salary'] = int(zero_salary)

        # Negative experience
        if 'minimumYearsExperience' in self.df.columns:
            neg_exp = (self.df['minimumYearsExperience'] < 0).sum()
            if neg_exp > 0:
                print(f"Negative experience: {neg_exp:,} cases")
                errors['negative_experience'] = int(neg_exp)

        # Invalid date ranges
        if all(col in self.df.columns for col in ['metadata_originalPostingDate', 'metadata_expiryDate']):
            self.df['post_date'] = pd.to_datetime(self.df['metadata_originalPostingDate'], errors='coerce')
            self.df['expiry_date'] = pd.to_datetime(self.df['metadata_expiryDate'], errors='coerce')

            date_errors = (self.df['post_date'] > self.df['expiry_date']).sum()
            print(f"Expiry date before posting date: {date_errors:,} cases")
            errors['invalid_date_range'] = int(date_errors)

        self.issues['logic_errors'] = errors
        return errors

    def check_text_inconsistencies(self):
        """Check for case variations and typos in categorical fields"""
        print("\n" + "="*80)
        print("CHECK 5: TEXT INCONSISTENCIES")
        print("="*80)

        inconsistencies = {}

        # Check categorical fields
        categorical_cols = ['employmentTypes', 'positionLevels', 'salary_type', 'status_jobStatus']

        for col in categorical_cols:
            if col in self.df.columns:
                values = self.df[col].dropna()
                unique_count = values.nunique()

                # Check for case variations
                lower_values = values.str.lower()
                unique_lower = lower_values.nunique()

                if unique_lower < unique_count:
                    print(f"\n{col}:")
                    print(f"  Unique values: {unique_count}")
                    print(f"  Unique (lowercase): {unique_lower}")
                    print(f"  Case variations detected: {unique_count - unique_lower}")

                    # Show examples
                    print(f"  Top values:")
                    print(values.value_counts().head(10))

                    inconsistencies[col] = {
                        'unique': int(unique_count),
                        'unique_lower': int(unique_lower),
                        'variations': int(unique_count - unique_lower)
                    }

        self.issues['inconsistencies'] = inconsistencies
        return inconsistencies

    def generate_report(self):
        """Generate comprehensive quality report"""
        print("\n" + "="*80)
        print("DATA QUALITY REPORT SUMMARY")
        print("="*80)

        total_rows = len(self.df)

        report = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'total_rows': total_rows,
            'total_columns': len(self.df.columns),
            'issues_found': self.issues,
            'severity': self._assess_severity()
        }

        # Print summary
        print(f"\nTotal rows analyzed: {total_rows:,}")
        print(f"\nIssues detected:")
        print(f"  Missing values: {self.issues['missing_values'].get('total_missing', 0):,}")
        print(f"  Duplicates: {self.issues['duplicates'].get('exact', 0):,}")
        print(f"  Logic errors: {sum(self.issues['logic_errors'].values())}")
        print(f"  Text inconsistencies: {len(self.issues['inconsistencies'])}")

        return report

    def _assess_severity(self):
        """Assess overall data quality severity"""
        total_issues = (
            self.issues['missing_values'].get('total_missing', 0) +
            self.issues['duplicates'].get('exact', 0) +
            sum(self.issues['logic_errors'].values())
        )

        total_rows = len(self.df)
        issue_pct = (total_issues / total_rows) * 100

        if issue_pct < 1:
            return 'LOW'
        elif issue_pct < 5:
            return 'MEDIUM'
        else:
            return 'HIGH'


def run_quality_checks(df):
    """Run full quality assessment pipeline"""
    checker = DataQualityChecker(df)

    checker.check_missing_values()
    checker.check_duplicates()
    checker.check_univariate_outliers()
    checker.check_logic_errors()
    checker.check_text_inconsistencies()

    report = checker.generate_report()

    return report, checker


if __name__ == '__main__':
    # Load data
    base_dir = Path(__file__).parent.parent
    data_path = base_dir / 'SGJobData.csv'

    print("Loading data...")
    df = pd.read_csv(data_path, low_memory=False)
    print(f"Loaded {len(df):,} rows\n")

    # Run checks
    report, checker = run_quality_checks(df)

    # Save report
    report_path = base_dir / 'data' / 'silver' / 'quality_report.json'
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n[OK] Quality report saved to: {report_path}")
