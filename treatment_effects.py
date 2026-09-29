import numpy as np
import pandas as pd
from scipy import stats

def run_analysis():
    df = pd.read_csv('hillstrom_cleaned.csv')
    
    # Define groups
    mens_df = df[df['segment'] == 'Mens E-Mail']
    womens_df = df[df['segment'] == 'Womens E-Mail']
    ctrl_df = df[df['segment'] == 'No E-Mail']
    
    # ---------------------------------------------------------
    # Helper functions
    # ---------------------------------------------------------
    def prop_test_wald_ci(s1, s2):
        n1, n2 = len(s1), len(s2)
        x1, x2 = s1.sum(), s2.sum()
        p1, p2 = x1 / n1, x2 / n2
        diff = p1 - p2
        rel_lift = (diff / p2) * 100 if p2 > 0 else np.nan
        
        # Wald CI
        se_wald = np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
        ci_lower = diff - 1.95996 * se_wald
        ci_upper = diff + 1.95996 * se_wald
        
        # Pooled z-test for p-value
        p_pool = (x1 + x2) / (n1 + n2)
        se_pool = np.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
        z_stat = diff / se_pool
        p_val = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        
        return {
            'n1': n1, 'n2': n2,
            'mean1': p1, 'mean2': p2,
            'diff': diff, 'rel_lift': rel_lift,
            'se': se_wald, 'ci_lower': ci_lower, 'ci_upper': ci_upper,
            'test_stat': z_stat, 'p_val': p_val
        }
        
    def spend_analysis(s1, s2, n_boot=10000, n_perm=10000, seed=42):
        n1, n2 = len(s1), len(s2)
        y1, y2 = s1.values, s2.values
        m1, m2 = np.mean(y1), np.mean(y2)
        diff = m1 - m2
        rel_lift = (diff / m2) * 100 if m2 > 0 else np.nan
        
        # Welch t-test
        t_res = stats.ttest_ind(y1, y2, equal_var=False)
        v1, v2 = np.var(y1, ddof=1), np.var(y2, ddof=1)
        se_welch = np.sqrt(v1/n1 + v2/n2)
        df_welch = ((v1/n1 + v2/n2)**2) / ((v1/n1)**2 / (n1 - 1) + (v2/n2)**2 / (n2 - 1))
        t_crit = stats.t.ppf(0.975, df=df_welch)
        welch_ci_lower = diff - t_crit * se_welch
        welch_ci_upper = diff + t_crit * se_welch
        
        # Percentile Bootstrap CI (n_boot resamples)
        rng = np.random.default_rng(seed)
        boot_y1 = rng.choice(y1, size=(n_boot, n1), replace=True)
        boot_y2 = rng.choice(y2, size=(n_boot, n2), replace=True)
        boot_diffs = boot_y1.mean(axis=1) - boot_y2.mean(axis=1)
        boot_ci_lower = np.percentile(boot_diffs, 2.5)
        boot_ci_upper = np.percentile(boot_diffs, 97.5)
        boot_se = np.std(boot_diffs)
        
        # Permutation test (n_perm resamples)
        pooled = np.concatenate([y1, y2])
        rng_perm = np.random.default_rng(seed)
        perm_diffs = np.empty(n_perm)
        for i in range(n_perm):
            shuffled = rng_perm.permutation(pooled)
            perm_diffs[i] = shuffled[:n1].mean() - shuffled[n1:].mean()
        perm_p_val = np.mean(np.abs(perm_diffs) >= np.abs(diff))
        
        return {
            'n1': n1, 'n2': n2,
            'mean1': m1, 'mean2': m2,
            'diff': diff, 'rel_lift': rel_lift,
            'welch_se': se_welch, 'welch_t': t_res.statistic, 'welch_df': df_welch,
            'welch_p': t_res.pvalue, 'welch_ci': (welch_ci_lower, welch_ci_upper),
            'boot_ci': (boot_ci_lower, boot_ci_upper), 'boot_se': boot_se,
            'perm_p': perm_p_val
        }

    # ---------------------------------------------------------
    # 1 & 2. Compute Comparisons
    # ---------------------------------------------------------
    comparisons = [
        ('Mens E-Mail vs No E-Mail', mens_df, ctrl_df, 'Treatment vs Control'),
        ('Womens E-Mail vs No E-Mail', womens_df, ctrl_df, 'Treatment vs Control'),
        ('Mens E-Mail vs Womens E-Mail', mens_df, womens_df, 'Head-to-Head')
    ]
    
    results = []
    for comp_name, g1, g2, comp_type in comparisons:
        # Visit
        v_res = prop_test_wald_ci(g1['visit'], g2['visit'])
        results.append({
            'Comparison': comp_name, 'Comp_Type': comp_type, 'Outcome': 'visit',
            'n1': v_res['n1'], 'n2': v_res['n2'],
            'mean1': v_res['mean1'], 'mean2': v_res['mean2'],
            'diff': v_res['diff'], 'rel_lift': v_res['rel_lift'],
            'ci_lower': v_res['ci_lower'], 'ci_upper': v_res['ci_upper'],
            'raw_p': v_res['p_val'], 'method': 'Two-prop z-test / Wald CI',
            'extra': f"z={v_res['test_stat']:.4f}"
        })
        
        # Conversion
        c_res = prop_test_wald_ci(g1['conversion'], g2['conversion'])
        results.append({
            'Comparison': comp_name, 'Comp_Type': comp_type, 'Outcome': 'conversion',
            'n1': c_res['n1'], 'n2': c_res['n2'],
            'mean1': c_res['mean1'], 'mean2': c_res['mean2'],
            'diff': c_res['diff'], 'rel_lift': c_res['rel_lift'],
            'ci_lower': c_res['ci_lower'], 'ci_upper': c_res['ci_upper'],
            'raw_p': c_res['p_val'], 'method': 'Two-prop z-test / Wald CI',
            'extra': f"z={c_res['test_stat']:.4f}"
        })
        
        # Spend
        s_res = spend_analysis(g1['spend'], g2['spend'])
        results.append({
            'Comparison': comp_name, 'Comp_Type': comp_type, 'Outcome': 'spend',
            'n1': s_res['n1'], 'n2': s_res['n2'],
            'mean1': s_res['mean1'], 'mean2': s_res['mean2'],
            'diff': s_res['diff'], 'rel_lift': s_res['rel_lift'],
            'ci_lower': s_res['boot_ci'][0], 'ci_upper': s_res['boot_ci'][1],
            'welch_ci_lower': s_res['welch_ci'][0], 'welch_ci_upper': s_res['welch_ci'][1],
            'raw_p': s_res['welch_p'], 'perm_p': s_res['perm_p'],
            'method': 'Bootstrap percentile CI (10k) & Welch/Permutation test',
            'extra': f"Welch t={s_res['welch_t']:.4f}, p_welch={s_res['welch_p']:.4e}, p_perm={s_res['perm_p']:.4e}, boot_ci=[{s_res['boot_ci'][0]:.4f}, {s_res['boot_ci'][1]:.4f}], welch_ci=[{s_res['welch_ci'][0]:.4f}, {s_res['welch_ci'][1]:.4f}]"
        })

    res_df = pd.DataFrame(results)

    # ---------------------------------------------------------
    # 3. Multiple Comparison Correction (Holm Procedure)
    # ---------------------------------------------------------
    def apply_holm(df_subset):
        df_sub = df_subset.copy().sort_values('raw_p').reset_index(drop=True)
        m = len(df_sub)
        adj_p = []
        for i, row in df_sub.iterrows():
            k = i + 1
            # factor is (m - k + 1)
            raw = row['raw_p']
            val = (m - k + 1) * raw
            adj_p.append(val)
        # Enforce monotonicity: p_adj[i] = max(p_adj[i-1], p_adj[i])
        for i in range(1, m):
            adj_p[i] = max(adj_p[i], adj_p[i-1])
        adj_p = [min(1.0, p) for p in adj_p]
        df_sub['holm_p'] = adj_p
        df_sub['significant_05'] = df_sub['holm_p'] < 0.05
        return df_sub

    t_vs_c = apply_holm(res_df[res_df['Comp_Type'] == 'Treatment vs Control'])
    h2h = apply_holm(res_df[res_df['Comp_Type'] == 'Head-to-Head'])
    
    print("="*80)
    print("TREATMENT VS CONTROL RESULTS (WITH HOLM ADJUSTMENT)")
    print("="*80)
    for _, r in t_vs_c.iterrows():
        print(f"{r['Comparison']} | Outcome: {r['Outcome']}")
        print(f"  Means: Arm1={r['mean1']:.4f}, Arm2={r['mean2']:.4f}, Diff={r['diff']:.4f}, Rel Lift={r['rel_lift']:+.2f}%")
        print(f"  95% CI: [{r['ci_lower']:.4f}, {r['ci_upper']:.4f}]")
        print(f"  Raw p: {r['raw_p']:.4e} | Holm-adjusted p: {r['holm_p']:.4e} | Sig: {r['significant_05']}")
        print(f"  Details: {r['extra']}\n")

    print("="*80)
    print("HEAD-TO-HEAD RESULTS (WITH HOLM ADJUSTMENT)")
    print("="*80)
    for _, r in h2h.iterrows():
        print(f"{r['Comparison']} | Outcome: {r['Outcome']}")
        print(f"  Means: Arm1={r['mean1']:.4f}, Arm2={r['mean2']:.4f}, Diff={r['diff']:.4f}, Rel Lift={r['rel_lift']:+.2f}%")
        print(f"  95% CI: [{r['ci_lower']:.4f}, {r['ci_upper']:.4f}]")
        print(f"  Raw p: {r['raw_p']:.4e} | Holm-adjusted p: {r['holm_p']:.4e} | Sig: {r['significant_05']}")
        print(f"  Details: {r['extra']}\n")

    # ---------------------------------------------------------
    # 4. Business-scale translation per 1,000 customers
    # ---------------------------------------------------------
    print("="*80)
    print("BUSINESS-SCALE TRANSLATION (PER 1,000 CUSTOMERS EMAILED)")
    print("="*80)
    for _, r in t_vs_c.iterrows():
        diff_1k = r['diff'] * 1000
        ci_lower_1k = r['ci_lower'] * 1000
        ci_upper_1k = r['ci_upper'] * 1000
        unit = "visits" if r['Outcome'] == 'visit' else ("conversions" if r['Outcome'] == 'conversion' else "revenue ($)")
        print(f"{r['Comparison']} -> {r['Outcome'].upper()}:")
        print(f"  Incremental {unit} per 1,000 emailed: {diff_1k:+.2f} (95% CI: [{ci_lower_1k:+.2f}, {ci_upper_1k:+.2f}])\n")

    # ---------------------------------------------------------
    # 5. Sensitivity analysis on $499 spend value
    # ---------------------------------------------------------
    print("="*80)
    print("SENSITIVITY ANALYSIS ON THE 12 CUSTOMERS WITH SPEND == $499.00")
    print("="*80)
    scenarios = [
        ('Original ($499.00)', 499.00),
        ('Recoded to next-highest ($482.31)', 482.31),
        ('Recoded to hypothetical uncensored ($750.00)', 750.00)
    ]
    
    sens_records = []
    for sc_name, sc_val in scenarios:
        df_sens = df.copy()
        df_sens.loc[df_sens['spend'] == 499.0, 'spend'] = sc_val
        
        m_s = df_sens[df_sens['segment'] == 'Mens E-Mail']['spend']
        w_s = df_sens[df_sens['segment'] == 'Womens E-Mail']['spend']
        c_s = df_sens[df_sens['segment'] == 'No E-Mail']['spend']
        
        # Mens vs Control
        res_m = spend_analysis(m_s, c_s, n_boot=10000, n_perm=10000, seed=42)
        sens_records.append({
            'Scenario': sc_name, 'Comparison': 'Mens E-Mail vs No E-Mail',
            'Mean_T': res_m['mean1'], 'Mean_C': res_m['mean2'],
            'ATE ($)': res_m['diff'], 'Rel Lift (%)': res_m['rel_lift'],
            'Boot 95% CI': f"[{res_m['boot_ci'][0]:.4f}, {res_m['boot_ci'][1]:.4f}]",
            'Welch 95% CI': f"[{res_m['welch_ci'][0]:.4f}, {res_m['welch_ci'][1]:.4f}]",
            'Welch p': res_m['welch_p'], 'Perm p': res_m['perm_p']
        })
        
        # Womens vs Control
        res_w = spend_analysis(w_s, c_s, n_boot=10000, n_perm=10000, seed=42)
        sens_records.append({
            'Scenario': sc_name, 'Comparison': 'Womens E-Mail vs No E-Mail',
            'Mean_T': res_w['mean1'], 'Mean_C': res_w['mean2'],
            'ATE ($)': res_w['diff'], 'Rel Lift (%)': res_w['rel_lift'],
            'Boot 95% CI': f"[{res_w['boot_ci'][0]:.4f}, {res_w['boot_ci'][1]:.4f}]",
            'Welch 95% CI': f"[{res_w['welch_ci'][0]:.4f}, {res_w['welch_ci'][1]:.4f}]",
            'Welch p': res_w['welch_p'], 'Perm p': res_w['perm_p']
        })

    sens_df = pd.DataFrame(sens_records)
    print(sens_df.to_string(index=False))

if __name__ == '__main__':
    run_analysis()
