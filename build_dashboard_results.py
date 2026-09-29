import numpy as np
import pandas as pd
from scipy import stats
import json

def build_dashboard():
    df = pd.read_csv('hillstrom_cleaned.csv')
    
    # -------------------------------------------------------------
    # Derived variables
    # -------------------------------------------------------------
    def get_ph(row):
        if row['mens'] == 1 and row['womens'] == 0:
            return 'Mens-only'
        elif row['mens'] == 0 and row['womens'] == 1:
            return 'Womens-only'
        elif row['mens'] == 1 and row['womens'] == 1:
            return 'Both'
        else:
            return 'Neither'
    df['purchase_history'] = df.apply(get_ph, axis=1)

    q25, q50, q75 = df['history'].quantile([0.25, 0.50, 0.75])
    bins_hist = [-np.inf, q25, q50, q75, np.inf]
    labels_hist = ['hist_q1', 'hist_q2', 'hist_q3', 'hist_q4']
    df['history_bracket'] = pd.cut(df['history'], bins=bins_hist, labels=labels_hist)

    bins_rec = [0, 3, 6, 9, 12]
    labels_rec = ['rec_1_3', 'rec_4_6', 'rec_7_9', 'rec_10_12']
    df['recency_bracket'] = pd.cut(df['recency'], bins=bins_rec, labels=labels_rec)

    ctrl_df = df[df['segment'] == 'No E-Mail']
    mens_df = df[df['segment'] == 'Mens E-Mail']
    womens_df = df[df['segment'] == 'Womens E-Mail']

    # =============================================================
    # 1. Treatment vs Control (6 tests)
    # =============================================================
    # Family 1: Treatment vs Control
    t_vs_c_records = []
    comparisons_tc = [
        ('Mens E-Mail vs No E-Mail', mens_df, ctrl_df),
        ('Womens E-Mail vs No E-Mail', womens_df, ctrl_df)
    ]
    
    for comp_name, g1, g2 in comparisons_tc:
        n1, n2 = len(g1), len(g2)
        conv1, conv2 = int(g1['conversion'].sum()), int(g2['conversion'].sum())
        
        # Visit
        p1_v, p2_v = g1['visit'].mean(), g2['visit'].mean()
        diff_v = p1_v - p2_v
        se_v = np.sqrt(p1_v*(1-p1_v)/n1 + p2_v*(1-p2_v)/n2)
        z_v = diff_v / np.sqrt(((g1['visit'].sum()+g2['visit'].sum())/(n1+n2))*(1-((g1['visit'].sum()+g2['visit'].sum())/(n1+n2)))*(1/n1+1/n2))
        p_val_v = 2 * (1 - stats.norm.cdf(abs(z_v)))
        ci_v = [diff_v*100 - 1.95996*se_v*100, diff_v*100 + 1.95996*se_v*100]
        
        t_vs_c_records.append({
            'comparison': comp_name,
            'outcome': 'visit',
            'estimate': diff_v * 100,
            'unit': 'pp',
            'ci_95': [round(ci_v[0], 2), round(ci_v[1], 2)],
            'sample_sizes': {'n_treatment': n1, 'n_control': n2},
            'converter_counts': {'treatment_converters': conv1, 'control_converters': conv2},
            'raw_p': float(p_val_v),
            'test_family': 'treatment_vs_control'
        })
        
        # Conversion
        p1_c, p2_c = g1['conversion'].mean(), g2['conversion'].mean()
        diff_c = p1_c - p2_c
        se_c = np.sqrt(p1_c*(1-p1_c)/n1 + p2_c*(1-p2_c)/n2)
        z_c = diff_c / np.sqrt(((conv1+conv2)/(n1+n2))*(1-((conv1+conv2)/(n1+n2)))*(1/n1+1/n2))
        p_val_c = 2 * (1 - stats.norm.cdf(abs(z_c)))
        ci_c = [diff_c*100 - 1.95996*se_c*100, diff_c*100 + 1.95996*se_c*100]
        
        t_vs_c_records.append({
            'comparison': comp_name,
            'outcome': 'conversion',
            'estimate': diff_c * 100,
            'unit': 'pp',
            'ci_95': [round(ci_c[0], 2), round(ci_c[1], 2)],
            'sample_sizes': {'n_treatment': n1, 'n_control': n2},
            'converter_counts': {'treatment_converters': conv1, 'control_converters': conv2},
            'raw_p': float(p_val_c),
            'test_family': 'treatment_vs_control'
        })
        
        # Spend
        m1_s, m2_s = g1['spend'].mean(), g2['spend'].mean()
        diff_s = m1_s - m2_s
        t_res = stats.ttest_ind(g1['spend'], g2['spend'], equal_var=False)
        # Percentile bootstrap CI from step 1
        rng = np.random.default_rng(42)
        b1 = rng.choice(g1['spend'].values, size=(10000, n1), replace=True).mean(axis=1)
        b2 = rng.choice(g2['spend'].values, size=(10000, n2), replace=True).mean(axis=1)
        b_diff = b1 - b2
        ci_s = [np.percentile(b_diff, 2.5), np.percentile(b_diff, 97.5)]
        
        t_vs_c_records.append({
            'comparison': comp_name,
            'outcome': 'spend',
            'estimate': diff_s,
            'unit': '$',
            'ci_95': [round(ci_s[0], 4), round(ci_s[1], 4)],
            'sample_sizes': {'n_treatment': n1, 'n_control': n2},
            'converter_counts': {'treatment_converters': conv1, 'control_converters': conv2},
            'raw_p': float(t_res.pvalue),
            'test_family': 'treatment_vs_control'
        })

    # Apply Holm to Family 1
    t_vs_c_df = pd.DataFrame(t_vs_c_records).sort_values('raw_p').reset_index(drop=True)
    m = len(t_vs_c_df)
    adj_p = []
    for i, r in t_vs_c_df.iterrows():
        adj_p.append((m - i) * r['raw_p'])
    for i in range(1, m):
        adj_p[i] = max(adj_p[i], adj_p[i-1])
    t_vs_c_df['holm_p'] = [min(1.0, p) for p in adj_p]
    t_vs_c_df['evidence_label'] = np.where(t_vs_c_df['holm_p'] < 0.05, 'confirmed', 'exploratory')

    # =============================================================
    # 2. Overall Head-to-Head (3 tests)
    # =============================================================
    h2h_all_records = []
    n1, n2 = len(mens_df), len(womens_df)
    conv1, conv2 = int(mens_df['conversion'].sum()), int(womens_df['conversion'].sum())
    
    # Visit
    p1_v, p2_v = mens_df['visit'].mean(), womens_df['visit'].mean()
    diff_v = p1_v - p2_v
    se_v = np.sqrt(p1_v*(1-p1_v)/n1 + p2_v*(1-p2_v)/n2)
    z_v = diff_v / np.sqrt(((mens_df['visit'].sum()+womens_df['visit'].sum())/(n1+n2))*(1-((mens_df['visit'].sum()+womens_df['visit'].sum())/(n1+n2)))*(1/n1+1/n2))
    p_val_v = 2 * (1 - stats.norm.cdf(abs(z_v)))
    ci_v = [diff_v*100 - 1.95996*se_v*100, diff_v*100 + 1.95996*se_v*100]
    h2h_all_records.append({
        'comparison': 'Mens E-Mail vs Womens E-Mail',
        'outcome': 'visit',
        'estimate': diff_v * 100,
        'unit': 'pp',
        'ci_95': [round(ci_v[0], 2), round(ci_v[1], 2)],
        'sample_sizes': {'n_mens': n1, 'n_womens': n2},
        'converter_counts': {'mens_converters': conv1, 'womens_converters': conv2},
        'raw_p': float(p_val_v),
        'test_family': 'overall_head_to_head'
    })
    
    # Conversion
    p1_c, p2_c = mens_df['conversion'].mean(), womens_df['conversion'].mean()
    diff_c = p1_c - p2_c
    se_c = np.sqrt(p1_c*(1-p1_c)/n1 + p2_c*(1-p2_c)/n2)
    z_c = diff_c / np.sqrt(((conv1+conv2)/(n1+n2))*(1-((conv1+conv2)/(n1+n2)))*(1/n1+1/n2))
    p_val_c = 2 * (1 - stats.norm.cdf(abs(z_c)))
    ci_c = [diff_c*100 - 1.95996*se_c*100, diff_c*100 + 1.95996*se_c*100]
    h2h_all_records.append({
        'comparison': 'Mens E-Mail vs Womens E-Mail',
        'outcome': 'conversion',
        'estimate': diff_c * 100,
        'unit': 'pp',
        'ci_95': [round(ci_c[0], 2), round(ci_c[1], 2)],
        'sample_sizes': {'n_mens': n1, 'n_womens': n2},
        'converter_counts': {'mens_converters': conv1, 'womens_converters': conv2},
        'raw_p': float(p_val_c),
        'test_family': 'overall_head_to_head'
    })
    
    # Spend
    m1_s, m2_s = mens_df['spend'].mean(), womens_df['spend'].mean()
    diff_s = m1_s - m2_s
    t_res = stats.ttest_ind(mens_df['spend'], womens_df['spend'], equal_var=False)
    b1 = rng.choice(mens_df['spend'].values, size=(10000, n1), replace=True).mean(axis=1)
    b2 = rng.choice(womens_df['spend'].values, size=(10000, n2), replace=True).mean(axis=1)
    b_diff = b1 - b2
    ci_s = [np.percentile(b_diff, 2.5), np.percentile(b_diff, 97.5)]
    h2h_all_records.append({
        'comparison': 'Mens E-Mail vs Womens E-Mail',
        'outcome': 'spend',
        'estimate': diff_s,
        'unit': '$',
        'ci_95': [round(ci_s[0], 4), round(ci_s[1], 4)],
        'sample_sizes': {'n_mens': n1, 'n_womens': n2},
        'converter_counts': {'mens_converters': conv1, 'womens_converters': conv2},
        'raw_p': float(t_res.pvalue),
        'test_family': 'overall_head_to_head'
    })

    # Apply Holm to Family 2
    h2h_all_df = pd.DataFrame(h2h_all_records).sort_values('raw_p').reset_index(drop=True)
    m = len(h2h_all_df)
    adj_p = []
    for i, r in h2h_all_df.iterrows():
        adj_p.append((m - i) * r['raw_p'])
    for i in range(1, m):
        adj_p[i] = max(adj_p[i], adj_p[i-1])
    h2h_all_df['holm_p'] = [min(1.0, p) for p in adj_p]
    h2h_all_df['evidence_label'] = np.where(h2h_all_df['holm_p'] < 0.05, 'confirmed', 'exploratory')

    # =============================================================
    # 3. 18 Interaction Tests
    # =============================================================
    import statsmodels.api as sm
    modifiers = ['purchase_history', 'newbie', 'channel', 'zip_code', 'history_bracket', 'recency_bracket']
    outcomes = ['visit', 'conversion', 'spend']
    T_mens = (df['segment'] == 'Mens E-Mail').astype(float)
    T_womens = (df['segment'] == 'Womens E-Mail').astype(float)

    int_records = []
    for mod in modifiers:
        dummies = pd.get_dummies(df[mod], prefix=mod, drop_first=True, dtype=float)
        inter_m = dummies.multiply(T_mens, axis=0)
        inter_m.columns = [f'{c}_x_mens' for c in inter_m.columns]
        inter_w = dummies.multiply(T_womens, axis=0)
        inter_w.columns = [f'{c}_x_womens' for c in inter_w.columns]
        Z = pd.concat([pd.Series(1.0, index=df.index, name='const'), T_mens.rename('T_mens'), T_womens.rename('T_womens'), dummies, inter_m, inter_w], axis=1)
        inter_cols = inter_m.columns.tolist() + inter_w.columns.tolist()
        df_test = len(inter_cols)
        
        for out in outcomes:
            y = df[out].values
            model = sm.OLS(y, Z).fit(cov_type='HC3')
            r_mat = np.zeros((df_test, len(model.params)))
            for i, col in enumerate(inter_cols):
                r_mat[i, Z.columns.get_loc(col)] = 1.0
            wt = model.wald_test(r_mat, scalar=True)
            stat = float(wt.statistic.item() if hasattr(wt.statistic, 'item') else wt.statistic)
            p_val = float(wt.pvalue.item() if hasattr(wt.pvalue, 'item') else wt.pvalue)
            
            unit = 'pp' if out in ['visit', 'conversion'] else '$'
            int_records.append({
                'comparison': f"Treatment x {mod} Interaction",
                'outcome': out,
                'estimate': stat, # Wald Chi2 test statistic
                'unit': 'Wald Chi2',
                'ci_95': None,
                'sample_sizes': {'n_total': len(df), 'df_test': df_test},
                'converter_counts': {'total_converters': int(df['conversion'].sum())},
                'raw_p': p_val,
                'test_family': 'interaction_tests'
            })

    int_df = pd.DataFrame(int_records).sort_values('raw_p').reset_index(drop=True)
    m = len(int_df)
    adj_p = []
    for i, r in int_df.iterrows():
        adj_p.append((m - i) * r['raw_p'])
    for i in range(1, m):
        adj_p[i] = max(adj_p[i], adj_p[i-1])
    int_df['holm_p'] = [min(1.0, p) for p in adj_p]
    int_df['evidence_label'] = np.where(int_df['holm_p'] < 0.05, 'confirmed', 'exploratory')

    # =============================================================
    # 4. 9 Purchase-History Head-to-Head Tests
    # =============================================================
    sub_df = pd.read_csv('subgroup_estimates.csv')
    ph_sub = sub_df[sub_df['Modifier'] == 'purchase_history'].copy()
    
    ph_records = []
    for i, r in ph_sub.iterrows():
        unit = 'pp' if r['Outcome'] in ['visit', 'conversion'] else '$'
        ph_records.append({
            'comparison': f"Mens vs Womens within {r['Subgroup']}",
            'outcome': r['Outcome'],
            'estimate': float(r['ATE_Mens_vs_Womens']),
            'unit': unit,
            'ci_95': [round(float(r['CI_Low_Mens_vs_Womens']), 2 if unit=='pp' else 4),
                      round(float(r['CI_High_Mens_vs_Womens']), 2 if unit=='pp' else 4)],
            'sample_sizes': {'n_mens': int(r['N_Mens']), 'n_womens': int(r['N_Womens']), 'n_control': int(r['N_Control'])},
            'converter_counts': {'mens_converters': int(r['Conv_Mens']), 'womens_converters': int(r['Conv_Womens'])},
            'raw_p': float(r['P_Mens_vs_Womens']),
            'test_family': 'purchase_history_head_to_head'
        })
        
    ph_df = pd.DataFrame(ph_records).sort_values('raw_p').reset_index(drop=True)
    m = len(ph_df)
    adj_p = []
    for i, r in ph_df.iterrows():
        adj_p.append((m - i) * r['raw_p'])
    for i in range(1, m):
        adj_p[i] = max(adj_p[i], adj_p[i-1])
    ph_df['holm_p'] = [min(1.0, p) for p in adj_p]
    ph_df['evidence_label'] = np.where(ph_df['holm_p'] < 0.05, 'confirmed', 'exploratory')

    # =============================================================
    # 5. Break-Even Table
    # =============================================================
    # ATE Spend Mens vs Control = 0.769827, 95% CI Lower Bound = 0.4875
    # ATE Spend Womens vs Control = 0.424412, 95% CI Lower Bound = 0.1689
    margins = [0.20, 0.40, 0.60, 0.80, 1.00]
    be_table = []
    for m_val in margins:
        be_table.append({
            'gross_margin': m_val,
            'margin_pct': f"{int(m_val*100)}%",
            'mens_breakeven_point': round(0.769827 * m_val, 4),
            'mens_breakeven_conservative_low': round(0.4875 * m_val, 4),
            'womens_breakeven_point': round(0.424412 * m_val, 4),
            'womens_breakeven_conservative_low': round(0.1689 * m_val, 4),
            'unit': '$'
        })

    # =============================================================
    # 6. Strategy Comparison at Defaults (margin 0.40, cost 0.05)
    # =============================================================
    # Assumptions: gross_margin = 0.40, cost_per_email = 0.05
    # Consistent subgroup mean basis
    # Strategy (a): No email: $0.00
    # Strategy (b): Womens to everyone: 1000 * (0.424412 * 0.40 - 0.05) = $119.76 / 1k
    # Strategy (c): Mens to everyone: 1000 * (0.769827 * 0.40 - 0.05) = $257.93 / 1k
    # Strategy (d): In-sample purchase-history rule: $260.79 / 1k (lift over Mens All = +$2.86 / 1k)
    # Strategy (e): Fixed rule (Womens to Womens-only, Mens to everyone else): $260.79 / 1k (lift = +$2.86 / 1k)
    strat_table = [
        {
            'strategy_key': 'a',
            'strategy_name': 'No E-Mail',
            'incremental_profit_per_1k': 0.00,
            'lift_over_mens_all_per_1k': -257.93,
            'unit': '$'
        },
        {
            'strategy_key': 'b',
            'strategy_name': 'Womens E-Mail to Everyone',
            'incremental_profit_per_1k': 119.76,
            'lift_over_mens_all_per_1k': -138.17,
            'unit': '$'
        },
        {
            'strategy_key': 'c',
            'strategy_name': 'Mens E-Mail to Everyone',
            'incremental_profit_per_1k': 257.93,
            'lift_over_mens_all_per_1k': 0.00,
            'unit': '$'
        },
        {
            'strategy_key': 'd',
            'strategy_name': 'Data-Driven Purchase-History Rule (In-Sample)',
            'incremental_profit_per_1k': 260.79,
            'lift_over_mens_all_per_1k': 2.86,
            'unit': '$'
        },
        {
            'strategy_key': 'e',
            'strategy_name': 'Fixed Pre-Specified Rule (Womens to Womens-only, Mens to all others)',
            'incremental_profit_per_1k': 260.79,
            'lift_over_mens_all_per_1k': 2.86,
            'unit': '$'
        }
    ]

    # =============================================================
    # 7. Fixed-Rule Comparison: Policy (e) vs Policy (c)
    # =============================================================
    w_only = df[df['purchase_history'] == 'Womens-only']
    share_wo = len(w_only) / len(df)
    spend_w_wo = w_only[w_only['segment'] == 'Womens E-Mail']['spend'].values
    spend_m_wo = w_only[w_only['segment'] == 'Mens E-Mail']['spend'].values
    ate_diff_wo = np.mean(spend_w_wo) - np.mean(spend_m_wo)
    
    n_w, n_m = len(spend_w_wo), len(spend_m_wo)
    boot_w = rng.choice(spend_w_wo, size=(10000, n_w), replace=True).mean(axis=1)
    boot_m = rng.choice(spend_m_wo, size=(10000, n_m), replace=True).mean(axis=1)
    boot_diffs = boot_w - boot_m

    fixed_rule_comp = []
    for m_val in margins:
        val_point = 1000.0 * share_wo * m_val * ate_diff_wo
        b_vals = 1000.0 * share_wo * m_val * boot_diffs
        ci_low, ci_high = np.percentile(b_vals, [2.5, 97.5])
        fixed_rule_comp.append({
            'comparison': 'Policy (e) vs Policy (c)',
            'gross_margin': m_val,
            'margin_pct': f"{int(m_val*100)}%",
            'estimate_per_1k': round(val_point, 2),
            'unit': '$',
            'ci_95': [round(ci_low, 2), round(ci_high, 2)],
            'cost_per_email_status': 'Cancels out (both policies email 100% of customers)',
            'contains_zero': bool(ci_low <= 0 <= ci_high)
        })

    # =============================================================
    # 8. MDE Table
    # =============================================================
    crit_mde = 1.959964 + 0.841621
    mde_configs = [
        ('Mens E-Mail vs No E-Mail', 'Overall', mens_df, ctrl_df, ctrl_df),
        ('Womens E-Mail vs No E-Mail', 'Overall', womens_df, ctrl_df, ctrl_df),
        ('Mens E-Mail vs Womens E-Mail', 'Overall', mens_df, womens_df, ctrl_df),
        ('Mens E-Mail vs Womens E-Mail', 'Womens-only',
         w_only[w_only['segment'] == 'Mens E-Mail'],
         w_only[w_only['segment'] == 'Womens E-Mail'],
         w_only[w_only['segment'] == 'No E-Mail']),
        ('Mens E-Mail vs Womens E-Mail', 'Both',
         df[(df['purchase_history'] == 'Both') & (df['segment'] == 'Mens E-Mail')],
         df[(df['purchase_history'] == 'Both') & (df['segment'] == 'Womens E-Mail')],
         df[(df['purchase_history'] == 'Both') & (df['segment'] == 'No E-Mail')])
    ]
    
    mde_table = []
    for comp_name, scope, g1, g2, ref in mde_configs:
        n1, n2 = len(g1), len(g2)
        for out in ['visit', 'conversion', 'spend']:
            ctrl_mean = ref[out].mean()
            obs_diff = g1[out].mean() - g2[out].mean()
            
            if out in ['visit', 'conversion']:
                p0 = ctrl_mean
                se = np.sqrt(p0 * (1 - p0) * (1/n1 + 1/n2))
                mde_val = crit_mde * se
                unit = 'pp'
                mde_disp = mde_val * 100.0
                obs_disp = obs_diff * 100.0
                ctrl_disp = ctrl_mean * 100.0
                pct_ctrl = (mde_val / ctrl_mean) * 100.0
            else:
                s0 = ref[out].std(ddof=1)
                se = s0 * np.sqrt(1/n1 + 1/n2)
                mde_val = crit_mde * se
                unit = '$'
                mde_disp = mde_val
                obs_disp = obs_diff
                ctrl_disp = ctrl_mean
                pct_ctrl = (mde_val / ctrl_mean) * 100.0
                
            mde_table.append({
                'comparison': comp_name,
                'scope': scope,
                'outcome': out,
                'n_treatment': n1,
                'n_reference': n2,
                'control_mean': round(ctrl_disp, 4),
                'mde': round(mde_disp, 4),
                'unit': unit,
                'mde_pct_of_control': round(pct_ctrl, 2),
                'observed_diff': round(obs_disp, 4),
                'observed_exceeds_mde': bool(abs(obs_disp) >= mde_disp)
            })

    # =============================================================
    # 9. Limitations
    # =============================================================
    limitations = [
        {
            'item': 1,
            'title': 'No Direct Cost or Margin Data',
            'detail': 'The dataset records revenue (spend) only, without dispatch costs, creative production expenses, or product margin. All profit metrics rely on explicitly stated parameter assumptions.'
        },
        {
            'item': 2,
            'title': 'Short Two-Week Attribution Window',
            'detail': 'Outcomes are tracked over a 2-week post-dispatch window only. Any long-run effects—such as customer unsubscribes, brand decay, or delayed repeat purchases—are unobserved.'
        },
        {
            'item': 3,
            'title': 'Single Retailer & Historical Setting',
            'detail': 'Data reflects a 2008 email marketing campaign conducted by a single specialty apparel and merchandise catalog retailer. External validity to other product verticals or modern inbox/mobile environments is unproven.'
        },
        {
            'item': 4,
            'title': 'Spend Clustering / Truncation at $499',
            'detail': 'Spend is capped or clustered at exactly $499.00 (likely reflecting top-coding or maximum order limits). Sensitivity analysis confirms that trimming or log-transforming this value does not alter primary conclusions.'
        },
        {
            'item': 5,
            'title': 'Low Conversion Rate & High Variance on Spend',
            'detail': 'Only 578 customers converted across 64,000 customers (0.90% overall base rate). Spend has a massive zero-spike and heavy skew, making subgroup comparisons and revenue differences statistically imprecise.'
        },
        {
            'item': 6,
            'title': 'Observed Randomization Balance Only',
            'detail': 'Covariate balance (SMD < 0.015) was formally verified on recorded pre-treatment covariates only. Unmeasured customer characteristics cannot be directly audited.'
        }
    ]

    # Combine into full dictionary
    dashboard_dict = {
        'metadata': {
            'dataset': 'Hillstrom MineThatData E-Mail Analytics (hillstrom_cleaned.csv)',
            'total_customers': len(df),
            'random_seed': 42,
            'generation_timestamp': '2026-09-28'
        },
        'treatment_vs_control': t_vs_c_df.to_dict(orient='records'),
        'overall_head_to_head': h2h_all_df.to_dict(orient='records'),
        'interaction_tests': int_df.to_dict(orient='records'),
        'purchase_history_head_to_head': ph_df.to_dict(orient='records'),
        'break_even_table': be_table,
        'strategy_comparison_defaults': {
            'assumptions': {'gross_margin': 0.40, 'cost_per_email': 0.05},
            'strategies': strat_table
        },
        'fixed_rule_comparison': fixed_rule_comp,
        'minimum_detectable_effects': mde_table,
        'limitations': limitations
    }

    with open('dashboard_results.json', 'w') as f:
        json.dump(dashboard_dict, f, indent=2)
    print("Successfully built and saved 'dashboard_results.json'.")

if __name__ == '__main__':
    build_dashboard()
