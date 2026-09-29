import pandas as pd
import numpy as np
from scipy import stats

def run_audit():
    df = pd.read_csv('hillstrom_email_analytics.csv')
    
    print("=" * 80)
    print("1. SHAPE, DTYPES, MISSING VALUES, DUPLICATES")
    print("=" * 80)
    print(f"Dataset Shape: {df.shape[0]:,} rows, {df.shape[1]} columns\n")
    print("Column Data Types and Missing Values:")
    audit_summary = pd.DataFrame({
        'Dtype': df.dtypes,
        'Non-Null Count': df.notnull().sum(),
        'Missing Count': df.isnull().sum(),
        'Missing %': (df.isnull().sum() / len(df)) * 100
    })
    print(audit_summary.to_string())
    
    dup_first = df.duplicated().sum()
    dup_all = df.duplicated(keep=False).sum()
    print(f"\nExact Duplicate Rows (excluding first occurrence): {dup_first:,} ({dup_first / len(df) * 100:.3f}%)")
    print(f"Total Rows Involved in Exact Duplicates (all occurrences): {dup_all:,} ({dup_all / len(df) * 100:.3f}%)")
    
    print("\n" + "=" * 80)
    print("2. CATEGORICAL COLUMNS: UNIQUE VALUES AND COUNTS")
    print("=" * 80)
    # Categorical columns
    cat_cols = ['segment', 'channel', 'zip_code', 'history_segment', 'mens', 'womens', 'newbie']
    # Check what columns exist
    for col in cat_cols:
        if col in df.columns:
            print(f"\n--- Column: '{col}' (Distinct count: {df[col].nunique()}) ---")
            counts = df[col].value_counts(dropna=False)
            pcts = df[col].value_counts(dropna=False, normalize=True) * 100
            col_df = pd.DataFrame({'Count': counts, 'Percentage (%)': pcts.round(4)})
            print(col_df.to_string())

    print("\n" + "=" * 80)
    print("3. DISTRIBUTION SUMMARIES FOR NUMERIC COLUMNS")
    print("=" * 80)
    num_cols = ['recency', 'history', 'spend']
    for col in num_cols:
        if col in df.columns:
            s = df[col]
            q = s.quantile([0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99])
            print(f"\n--- Column: '{col}' ---")
            print(f"  Count:    {s.count():,}")
            print(f"  Min:      {s.min():.4f}")
            print(f"  Max:      {s.max():.4f}")
            print(f"  Mean:     {s.mean():.4f}")
            print(f"  Std Dev:  {s.std():.4f}")
            print(f"  Median:   {s.median():.4f}")
            print(f"  IQR:      {s.quantile(0.75) - s.quantile(0.25):.4f}")
            print(f"  Skewness: {s.skew():.4f}")
            print(f"  Kurtosis: {s.kurtosis():.4f}")
            print("  Selected Percentiles:")
            for p, val in q.items():
                print(f"    p{int(p*100):02d}: {val:.4f}")

    print("\n" + "=" * 80)
    print("4. OUTCOME BASE RATES OVERALL AND BY ARM")
    print("=" * 80)
    print(f"Total Population: N = {len(df):,}")
    print(f"Overall Visit Rate:      {df['visit'].mean()*100:.4f}% ({df['visit'].sum():,} / {len(df):,})")
    print(f"Overall Conversion Rate: {df['conversion'].mean()*100:.4f}% ({df['conversion'].sum():,} / {len(df):,})")
    print(f"Overall Mean Spend:      ${df['spend'].mean():.4f} (Std: ${df['spend'].std():.4f}, Total Spend: ${df['spend'].sum():,.2f})")
    
    print("\n--- Breakdown by Treatment Arm (segment) ---")
    arm_metrics = df.groupby('segment').agg(
        N=('visit', 'count'),
        Visits=('visit', 'sum'),
        Visit_Rate=('visit', lambda x: x.mean() * 100),
        Conversions=('conversion', 'sum'),
        Conv_Rate=('conversion', lambda x: x.mean() * 100),
        Total_Spend=('spend', 'sum'),
        Mean_Spend=('spend', 'mean'),
        Std_Spend=('spend', 'std')
    )
    print(arm_metrics.to_string())

    print("\n" + "=" * 80)
    print("5. SPEND DISTRIBUTION CHECK (ZERO-INFLATION & SKEWNESS)")
    print("=" * 80)
    zero_spend = (df['spend'] == 0).sum()
    zero_spend_pct = (df['spend'] == 0).mean() * 100
    pos_spend = (df['spend'] > 0).sum()
    pos_spend_pct = (df['spend'] > 0).mean() * 100
    print(f"Zero Spend Count:     {zero_spend:,} ({zero_spend_pct:.4f}%)")
    print(f"Positive Spend Count: {pos_spend:,} ({pos_spend_pct:.4f}%)")
    
    converters = df[df['conversion'] == 1]
    spend_pos = df[df['spend'] > 0]['spend']
    print(f"\n--- Spend Among Customers Who Converted (N = {len(converters):,}) ---")
    print(f"  Min:      ${converters['spend'].min():.4f}")
    print(f"  Max:      ${converters['spend'].max():.4f}")
    print(f"  Median:   ${converters['spend'].median():.4f}")
    print(f"  Mean:     ${converters['spend'].mean():.4f}")
    print(f"  Std Dev:  ${converters['spend'].std():.4f}")
    print(f"  Skewness: {converters['spend'].skew():.4f}")
    print(f"  Kurtosis: {converters['spend'].kurtosis():.4f}")
    print("  Percentiles among positive spenders:")
    for p in [0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99, 0.999]:
        print(f"    p{p*100:04.1f}%: ${spend_pos.quantile(p):.4f}")
    
    # Check top 10 spenders
    print("\nTop 10 highest spend observations:")
    top10 = df.sort_values(by='spend', ascending=False)[['segment', 'spend', 'conversion', 'visit', 'history', 'recency']].head(10)
    print(top10.to_string())

    print("\n" + "=" * 80)
    print("6. LOGIC CHECKS BETWEEN OUTCOME VARIABLES")
    print("=" * 80)
    c1 = (df['spend'] > 0) & (df['conversion'] == 0)
    c2 = (df['conversion'] == 1) & (df['spend'] == 0)
    c3 = (df['conversion'] == 1) & (df['visit'] == 0)
    c4 = (df['spend'] > 0) & (df['visit'] == 0)
    print(f"1) Customers with spend > 0 but conversion == 0: {c1.sum():,} rows")
    print(f"2) Customers with conversion == 1 but spend == 0: {c2.sum():,} rows")
    print(f"3) Customers with conversion == 1 but visit == 0: {c3.sum():,} rows")
    print(f"4) Customers with spend > 0 but visit == 0:      {c4.sum():,} rows")
    
    # Conversion vs Visit crosstab
    print("\nCrosstab: Visit vs Conversion")
    print(pd.crosstab(df['visit'], df['conversion'], margins=True))

    print("\n" + "=" * 80)
    print("7. TREATMENT ARM SIZES & RANDOMIZATION CHECK")
    print("=" * 80)
    arm_counts = df['segment'].value_counts()
    n_total = len(df)
    expected_n = n_total / 3.0
    expected_pct = 100.0 / 3.0
    
    arm_df = pd.DataFrame({
        'Observed Count': arm_counts,
        'Observed Pct (%)': (arm_counts / n_total * 100).round(4),
        'Expected Count': expected_n,
        'Expected Pct (%)': round(expected_pct, 4),
        'Diff (Obs - Exp)': arm_counts - expected_n,
        'Pct Diff (%)': ((arm_counts - expected_n) / expected_n * 100).round(4)
    })
    print(arm_df.to_string())
    
    chi2, p_val = stats.chisquare(arm_counts)
    print(f"\nChi-Square Goodness of Fit Test (Equal 1/3 ratio):")
    print(f"  Chi2 Statistic: {chi2:.4f}")
    print(f"  Degrees of Freedom: {len(arm_counts) - 1}")
    print(f"  P-value: {p_val:.4f}")

if __name__ == '__main__':
    run_audit()
