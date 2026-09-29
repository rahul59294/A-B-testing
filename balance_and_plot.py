import subprocess
orig_check_output = subprocess.check_output
def patched_check_output(cmd, *args, **kwargs):
    if isinstance(cmd, (list, tuple)) and len(cmd) > 0 and 'system_profiler' in cmd[0]:
        raise subprocess.CalledProcessError(1, cmd)
    return orig_check_output(cmd, *args, **kwargs)
subprocess.check_output = patched_check_output

import os
os.environ['MPLCONFIGDIR'] = '/tmp/mpl'
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import numpy as np
import pandas as pd
from scipy import stats, optimize

def main():
    # -------------------------------------------------------------
    # 1. Clean dataset & dummy columns
    # -------------------------------------------------------------
    df_raw = pd.read_csv('hillstrom_email_analytics.csv')
    df_clean = df_raw.copy()
    
    # Label fix: Surburban -> Suburban
    df_clean['zip_code'] = df_clean['zip_code'].replace({'Surburban': 'Suburban'})
    
    # Treatment indicator and dummies
    # Reference level: 'No E-Mail'
    df_clean['treatment_arm'] = pd.Categorical(
        df_clean['segment'], 
        categories=['No E-Mail', 'Mens E-Mail', 'Womens E-Mail'], 
        ordered=False
    )
    df_clean['treatment_mens'] = (df_clean['segment'] == 'Mens E-Mail').astype(int)
    df_clean['treatment_womens'] = (df_clean['segment'] == 'Womens E-Mail').astype(int)
    
    df_clean.to_csv('hillstrom_cleaned.csv', index=False)
    print("Saved 'hillstrom_cleaned.csv' successfully.")
    
    # -------------------------------------------------------------
    # 2. Covariate Balance Check (SMD & Love Plot)
    # -------------------------------------------------------------
    covariates_cont = ['recency', 'history']
    covariates_bin = ['mens', 'womens', 'newbie']
    covariates_cat = ['zip_code', 'channel', 'history_segment']
    
    feature_dict = {}
    for col in covariates_cont + covariates_bin:
        feature_dict[col] = df_clean[col].values
        
    for col in covariates_cat:
        dummies = pd.get_dummies(df_clean[col], prefix=col, drop_first=False)
        for c in dummies.columns:
            feature_dict[c] = dummies[c].astype(int).values
            
    features_df = pd.DataFrame(feature_dict)
    
    def compute_smd(g1, g2):
        m1, m2 = np.mean(g1), np.mean(g2)
        v1, v2 = np.var(g1, ddof=1), np.var(g2, ddof=1)
        s_pooled = np.sqrt((v1 + v2) / 2.0)
        return (m1 - m2) / s_pooled if s_pooled > 0 else 0.0

    idx_mens = (df_clean['segment'] == 'Mens E-Mail').values
    idx_womens = (df_clean['segment'] == 'Womens E-Mail').values
    idx_ctrl = (df_clean['segment'] == 'No E-Mail').values
    
    smd_records = []
    for col in features_df.columns:
        m = features_df[col].values[idx_mens]
        w = features_df[col].values[idx_womens]
        c = features_df[col].values[idx_ctrl]
        
        smd_m_c = compute_smd(m, c)
        smd_w_c = compute_smd(w, c)
        smd_m_w = compute_smd(m, w)
        max_abs = max(abs(smd_m_c), abs(smd_w_c), abs(smd_m_w))
        
        smd_records.append({
            'Covariate': col,
            'Mens vs No E-Mail': smd_m_c,
            'Womens vs No E-Mail': smd_w_c,
            'Mens vs Womens': smd_m_w,
            'Max |SMD|': max_abs,
            'Flag (|SMD| > 0.1)': max_abs > 0.1
        })
        
    smd_table = pd.DataFrame(smd_records)
    print("\n" + "="*80)
    print("STANDARDIZED MEAN DIFFERENCES (SMD) ACROSS PRE-TREATMENT COVARIATES")
    print("="*80)
    print(smd_table.to_string(index=False))
    
    flagged = smd_table[smd_table['Flag (|SMD| > 0.1)']]
    if len(flagged) == 0:
        print("\n--> Balance Verification: ZERO covariates have |SMD| > 0.10. Excellent balance!")
    else:
        print(f"\n--> Flagged covariates with |SMD| > 0.10:\n{flagged}")

    # Produce Love Plot
    label_map = {
        'recency': 'Recency (Months)',
        'history': 'Historical Spend ($)',
        'mens': 'Past Mens Buyer',
        'womens': 'Past Womens Buyer',
        'newbie': 'Newbie Customer (<12m)',
        'zip_code_Rural': 'Zip: Rural',
        'zip_code_Suburban': 'Zip: Suburban',
        'zip_code_Urban': 'Zip: Urban',
        'channel_Multichannel': 'Channel: Multichannel',
        'channel_Phone': 'Channel: Phone',
        'channel_Web': 'Channel: Web',
        'history_segment_1) $0 - $100': 'History Bracket: $0 - $100',
        'history_segment_2) $100 - $200': 'History Bracket: $100 - $200',
        'history_segment_3) $200 - $350': 'History Bracket: $200 - $350',
        'history_segment_4) $350 - $500': 'History Bracket: $350 - $500',
        'history_segment_5) $500 - $750': 'History Bracket: $500 - $750',
        'history_segment_6) $750 - $1,000': 'History Bracket: $750 - $1,000',
        'history_segment_7) $1,000 +': 'History Bracket: $1,000 +'
    }
    plot_df = smd_table.copy()
    plot_df['Label'] = plot_df['Covariate'].map(label_map)
    plot_df = plot_df.sort_values(by='Max |SMD|', ascending=True).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(10, 8.5), dpi=300)
    y_pos = np.arange(len(plot_df))
    offset = 0.22

    ax.scatter(plot_df['Mens vs No E-Mail'], y_pos + offset, color='#1f77b4', label='Mens E-Mail vs No E-Mail', s=65, alpha=0.9, marker='o')
    ax.scatter(plot_df['Womens vs No E-Mail'], y_pos, color='#ff7f0e', label='Womens E-Mail vs No E-Mail', s=65, alpha=0.9, marker='s')
    ax.scatter(plot_df['Mens vs Womens'], y_pos - offset, color='#2ca02c', label='Mens E-Mail vs Womens E-Mail', s=65, alpha=0.9, marker='^')

    ax.axvline(0, color='gray', linestyle='-', linewidth=0.8, alpha=0.7)
    ax.axvline(-0.1, color='#d62728', linestyle='--', linewidth=1.2, label='Threshold (|SMD| = 0.10)')
    ax.axvline(0.1, color='#d62728', linestyle='--', linewidth=1.2)
    ax.axvspan(-0.1, 0.1, color='#2ca02c', alpha=0.08, label='Balance Region (|SMD| ≤ 0.10)')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(plot_df['Label'], fontsize=10)
    ax.set_xlim(-0.15, 0.15)
    ax.set_xlabel('Standardized Mean Difference (SMD)', fontsize=11, fontweight='bold', labelpad=10)
    ax.set_title('Love Plot: Pre-Treatment Covariate Balance Across Treatment Arms', fontsize=13, fontweight='bold', pad=14)
    ax.grid(axis='both', linestyle=':', alpha=0.5)
    ax.legend(loc='lower right', frameon=True, framealpha=0.92, fontsize=9.5)

    plt.tight_layout()
    fig.savefig('love_plot.png', dpi=300)
    plt.close()
    print("Saved Love plot as 'love_plot.png'.")

    # -------------------------------------------------------------
    # 3. Omnibus Test: Multinomial Logistic Regression LRT
    # -------------------------------------------------------------
    arm_map = {'No E-Mail': 0, 'Mens E-Mail': 1, 'Womens E-Mail': 2}
    y = df_clean['segment'].map(arm_map).values
    
    # Covariates with 1 reference category dropped per factor
    cov_list = [
        df_clean[['recency', 'history', 'mens', 'womens', 'newbie']],
        pd.get_dummies(df_clean['zip_code'], prefix='zip', drop_first=True, dtype=float),
        pd.get_dummies(df_clean['channel'], prefix='chan', drop_first=True, dtype=float),
        pd.get_dummies(df_clean['history_segment'], prefix='hist_seg', drop_first=True, dtype=float)
    ]
    X_mat = pd.concat(cov_list, axis=1)
    n_samples, n_features = X_mat.shape
    
    # Null log-likelihood
    counts = np.bincount(y)
    p_null = counts / len(y)
    ll_null = np.sum(counts * np.log(p_null))
    
    # Full model MLE via scipy
    X_std = (X_mat.values - X_mat.mean(axis=0).values) / X_mat.std(axis=0).values
    X_des = np.column_stack([np.ones(n_samples), X_std])
    n_params_per_arm = n_features + 1

    def mnl_loss_grad(params):
        b1 = params[:n_params_per_arm]
        b2 = params[n_params_per_arm:]
        eta1 = X_des @ b1
        eta2 = X_des @ b2
        max_eta = np.maximum(0, np.maximum(eta1, eta2))
        sum_exp = np.exp(-max_eta) + np.exp(eta1 - max_eta) + np.exp(eta2 - max_eta)
        log_denom = max_eta + np.log(sum_exp)
        log_p0 = -log_denom
        log_p1 = eta1 - log_denom
        log_p2 = eta2 - log_denom
        p0 = np.exp(log_p0)
        p1 = np.exp(log_p1)
        p2 = np.exp(log_p2)
        nll = -np.sum(np.where(y == 0, log_p0, np.where(y == 1, log_p1, log_p2)))
        grad1 = X_des.T @ (p1 - (y == 1).astype(float))
        grad2 = X_des.T @ (p2 - (y == 2).astype(float))
        return nll, np.concatenate([grad1, grad2])

    init_params = np.zeros(2 * n_params_per_arm)
    init_params[0] = np.log(counts[1] / counts[0])
    init_params[n_params_per_arm] = np.log(counts[2] / counts[0])

    res = optimize.minimize(mnl_loss_grad, init_params, jac=True, method='L-BFGS-B', options={'ftol': 1e-15, 'gtol': 1e-8})
    ll_full = -res.fun
    lr_stat = 2 * (ll_full - ll_null)
    df_lrt = 2 * n_features
    p_val = stats.chi2.sf(lr_stat, df=df_lrt)

    print("\n" + "="*80)
    print("OMNIBUS TEST: MULTINOMIAL LOGISTIC REGRESSION LIKELIHOOD-RATIO TEST")
    print("="*80)
    print(f"Null Model Log-Likelihood (Intercept-only): {ll_null:.4f}")
    print(f"Full Model Log-Likelihood (All Covariates): {ll_full:.4f}")
    print(f"Likelihood-Ratio Test Statistic (Chi2):    {lr_stat:.4f}")
    print(f"Degrees of Freedom:                        {df_lrt}")
    print(f"P-value:                                   {p_val:.4f}")
    print(f"Conclusion: Randomization is {'BALANCED (p > 0.05)' if p_val > 0.05 else 'IMBALANCED (p <= 0.05)'}.")

    # -------------------------------------------------------------
    # 4. Descriptive Check on $499 Spend Value
    # -------------------------------------------------------------
    print("\n" + "="*80)
    print("DESCRIPTIVE CHECK ON POSITIVE SPEND VALUES AND $499.00")
    print("="*80)
    pos_spend = df_clean[df_clean['spend'] > 0]
    top10_spend = pos_spend['spend'].value_counts().head(10)
    top10_df = pd.DataFrame({
        'Rank': range(1, 11),
        'Spend Value ($)': top10_spend.index,
        'Frequency (Count)': top10_spend.values,
        'Share of All Positive Spenders (%)': (top10_spend.values / len(pos_spend) * 100).round(2)
    })
    print("\nTop 10 Most Frequent Positive Spend Values:")
    print(top10_df.to_string(index=False))

    at_499 = df_clean[df_clean['spend'] == 499.0]
    print(f"\nTotal Customers with spend == $499.00: {len(at_499)}")
    split_499 = at_499['segment'].value_counts()
    
    # Arm totals among converters
    converters_by_arm = df_clean[df_clean['conversion'] == 1]['segment'].value_counts()
    customers_by_arm = df_clean['segment'].value_counts()
    
    split_df = pd.DataFrame({
        'Count at $499': split_499,
        'Total Converters in Arm': converters_by_arm,
        '% of Arm Converters at $499': (split_499 / converters_by_arm * 100).round(2),
        'Total Customers in Arm': customers_by_arm,
        '% of All Arm Customers at $499': (split_499 / customers_by_arm * 100).round(4)
    })
    print("\nBreakdown of the 12 Customers at $499.00 Across Treatment Arms:")
    print(split_df.to_string())

if __name__ == '__main__':
    main()
