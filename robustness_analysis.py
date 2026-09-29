import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

def main():
    df = pd.read_csv('hillstrom_cleaned.csv')
    
    # -------------------------------------------------------------
    # 1. Prepare Covariates and Lin (2013) Estimator
    # -------------------------------------------------------------
    # Pre-treatment covariates
    # recency, history, mens, womens, newbie, zip_code dummies, channel dummies
    cov_num = ['recency', 'history']
    cov_bin = ['mens', 'womens', 'newbie']
    
    # Create dummies (drop first to avoid collinearity)
    zip_dummies = pd.get_dummies(df['zip_code'], prefix='zip', drop_first=True, dtype=float)
    chan_dummies = pd.get_dummies(df['channel'], prefix='chan', drop_first=True, dtype=float)
    
    X_raw = pd.concat([df[cov_num + cov_bin], zip_dummies, chan_dummies], axis=1)
    
    # Mean-center all covariates (Lin 2013 requirement)
    X_centered = X_raw - X_raw.mean(axis=0)
    
    # Treatment dummies
    T_mens = (df['segment'] == 'Mens E-Mail').astype(float)
    T_womens = (df['segment'] == 'Womens E-Mail').astype(float)
    
    # Interactions
    inter_mens = X_centered.multiply(T_mens, axis=0)
    inter_mens.columns = [f"{c}_x_mens" for c in inter_mens.columns]
    
    inter_womens = X_centered.multiply(T_womens, axis=0)
    inter_womens.columns = [f"{c}_x_womens" for c in inter_womens.columns]
    
    # Design matrix: Intercept, T_mens, T_womens, X_centered, inter_mens, inter_womens
    Z = pd.concat([
        pd.Series(1.0, index=df.index, name='const'),
        T_mens.rename('T_mens'),
        T_womens.rename('T_womens'),
        X_centered,
        inter_mens,
        inter_womens
    ], axis=1)
    
    print(f"Lin (2013) Design Matrix shape: {Z.shape}")
    print(f"Number of covariates: {X_centered.shape[1]}")
    
    # -------------------------------------------------------------
    # Fit Lin (2013) OLS with HC3 for each outcome
    # -------------------------------------------------------------
    outcomes = ['visit', 'conversion', 'spend']
    adj_results = {}
    
    for outcome in outcomes:
        y = df[outcome].values
        model = sm.OLS(y, Z).fit(cov_type='HC3')
        
        # Mens vs Control
        ate_m = model.params['T_mens']
        se_m = model.bse['T_mens']
        ci_m = model.conf_int().loc['T_mens']
        p_m = model.pvalues['T_mens']
        
        # Womens vs Control
        ate_w = model.params['T_womens']
        se_w = model.bse['T_womens']
        ci_w = model.conf_int().loc['T_womens']
        p_w = model.pvalues['T_womens']
        
        # Head to Head: Mens vs Womens (tau_m - tau_w)
        # Using linear hypothesis / contrast
        contrast = np.zeros(len(model.params))
        contrast[Z.columns.get_loc('T_mens')] = 1.0
        contrast[Z.columns.get_loc('T_womens')] = -1.0
        
        t_test = model.t_test(contrast)
        ate_h2h = float(t_test.effect.item() if hasattr(t_test.effect, 'item') else t_test.effect)
        se_h2h = float(t_test.sd.item() if hasattr(t_test.sd, 'item') else t_test.sd)
        p_h2h = float(t_test.pvalue.item() if hasattr(t_test.pvalue, 'item') else t_test.pvalue)
        # 95% CI
        ci_h2h_low = ate_h2h - 1.95996 * se_h2h
        ci_h2h_high = ate_h2h + 1.95996 * se_h2h
        
        adj_results[outcome] = {
            'mens_vs_ctrl': {'ate': ate_m, 'se': se_m, 'ci_low': ci_m[0], 'ci_high': ci_m[1], 'p': p_m},
            'womens_vs_ctrl': {'ate': ate_w, 'se': se_w, 'ci_low': ci_w[0], 'ci_high': ci_w[1], 'p': p_w},
            'h2h': {'ate': ate_h2h, 'se': se_h2h, 'ci_low': ci_h2h_low, 'ci_high': ci_h2h_high, 'p': p_h2h},
            'r2': model.rsquared
        }
        
    # Unadjusted results from previous step:
    # Mens vs Ctrl:
    # visit: diff = 0.07658957, ci = [0.06995, 0.08323]
    # conv: diff = 0.00680500, ci = [0.00500, 0.00861]
    # spend: diff = 0.76982736, welch_ci = [0.4851, 1.0545] (boot: [0.4875, 1.0589])
    # Womens vs Ctrl:
    # visit: diff = 0.04523310, ci = [0.03889, 0.05157]
    # conv: diff = 0.00311105, ci = [0.00150, 0.00472]
    # spend: diff = 0.42441221, welch_ci = [0.1690, 0.6799] (boot: [0.1689, 0.6821])
    # Head to head:
    # visit: diff = 0.03135647, ci = [0.02432, 0.03839]
    # conv: diff = 0.00369395, ci = [0.00174, 0.00565]
    # spend: diff = 0.34541515, welch_ci = [0.0326, 0.6583] (boot: [0.0316, 0.6582])
    
    unadj = {
        'visit': {
            'mens_vs_ctrl': {'ate': 0.07658957, 'ci_low': 0.069947, 'ci_high': 0.083232, 'p': 0.0},
            'womens_vs_ctrl': {'ate': 0.04523310, 'ci_low': 0.038894, 'ci_high': 0.051572, 'p': 0.0},
            'h2h': {'ate': 0.03135647, 'ci_low': 0.024323, 'ci_high': 0.038390, 'p': 3.82e-18}
        },
        'conversion': {
            'mens_vs_ctrl': {'ate': 0.00680500, 'ci_low': 0.004997, 'ci_high': 0.008613, 'p': 1.52e-13},
            'womens_vs_ctrl': {'ate': 0.00311105, 'ci_low': 0.001499, 'ci_high': 0.004723, 'p': 1.57e-4},
            'h2h': {'ate': 0.00369395, 'ci_low': 0.001743, 'ci_high': 0.005645, 'p': 2.05e-4}
        },
        'spend': {
            'mens_vs_ctrl': {'ate': 0.76982736, 'ci_low': 0.485121, 'ci_high': 1.054534, 'p': 1.16e-7},
            'womens_vs_ctrl': {'ate': 0.42441221, 'ci_low': 0.168965, 'ci_high': 0.679860, 'p': 1.13e-3},
            'h2h': {'ate': 0.34541515, 'ci_low': 0.032560, 'ci_high': 0.658270, 'p': 3.05e-2}
        }
    }
    
    print("\n" + "="*90)
    print("COMPARISON: UNADJUSTED VS LIN (2013) REGRESSION-ADJUSTED ATES")
    print("="*90)
    
    rows = []
    for outcome in outcomes:
        for comp_key, comp_name in [('mens_vs_ctrl', 'Mens E-Mail vs No E-Mail'), ('womens_vs_ctrl', 'Womens E-Mail vs No E-Mail')]:
            u = unadj[outcome][comp_key]
            a = adj_results[outcome][comp_key]
            
            u_ate, a_ate = u['ate'], a['ate']
            diff_ate = a_ate - u_ate
            
            u_width = u['ci_high'] - u['ci_low']
            a_width = a['ci_high'] - a['ci_low']
            pct_change_width = ((a_width - u_width) / u_width) * 100
            
            rows.append({
                'Comparison': comp_name,
                'Outcome': outcome,
                'Unadjusted ATE': u_ate,
                'Unadjusted 95% CI': f"[{u['ci_low']:.4f}, {u['ci_high']:.4f}]",
                'Adjusted ATE': a_ate,
                'Adjusted 95% CI': f"[{a['ci_low']:.4f}, {a['ci_high']:.4f}]",
                'Diff (Adj - Unadj)': diff_ate,
                'Unadj Width': u_width,
                'Adj Width': a_width,
                'CI Width Change (%)': pct_change_width,
                'Adj p-value': a['p']
            })
            
    comp_df = pd.DataFrame(rows)
    print(comp_df.to_string(index=False))
    
    # -------------------------------------------------------------
    # 3. Head to Head Mens vs Womens (Adjusted + Holm)
    # -------------------------------------------------------------
    print("\n" + "="*90)
    print("HEAD-TO-HEAD: MENS VS WOMENS (ADJUSTED + HOLM ADJUSTMENT)")
    print("="*90)
    h2h_rows = []
    for outcome in outcomes:
        u = unadj[outcome]['h2h']
        a = adj_results[outcome]['h2h']
        
        u_ate, a_ate = u['ate'], a['ate']
        diff_ate = a_ate - u_ate
        u_width = u['ci_high'] - u['ci_low']
        a_width = a['ci_high'] - a['ci_low']
        pct_change_width = ((a_width - u_width) / u_width) * 100
        
        h2h_rows.append({
            'Outcome': outcome,
            'Unadj ATE': u_ate,
            'Unadj 95% CI': f"[{u['ci_low']:.4f}, {u['ci_high']:.4f}]",
            'Adj ATE': a_ate,
            'Adj 95% CI': f"[{a['ci_low']:.4f}, {a['ci_high']:.4f}]",
            'Diff (Adj - Unadj)': diff_ate,
            'CI Width Change (%)': pct_change_width,
            'Raw p': a['p']
        })
    h2h_df = pd.DataFrame(h2h_rows).sort_values('Raw p').reset_index(drop=True)
    
    # Apply Holm to the 3 tests
    m = len(h2h_df)
    adj_p = []
    for i, row in h2h_df.iterrows():
        k = i + 1
        adj_p.append((m - k + 1) * row['Raw p'])
    for i in range(1, m):
        adj_p[i] = max(adj_p[i], adj_p[i-1])
    h2h_df['Holm p'] = [min(1.0, p) for p in adj_p]
    h2h_df['Survives Holm (0.05)'] = h2h_df['Holm p'] < 0.05
    print(h2h_df.to_string(index=False))

    # -------------------------------------------------------------
    # 4. Basket Size Analysis & Spend ATE Decomposition
    # -------------------------------------------------------------
    print("\n" + "="*90)
    print("BASKET SIZE ANALYSIS (CONDITIONAL ON CONVERSION) & SPEND ATE DECOMPOSITION")
    print("="*90)
    
    # Average spend per converter by arm
    rng = np.random.default_rng(42)
    n_boot = 10000
    
    arms = ['No E-Mail', 'Womens E-Mail', 'Mens E-Mail']
    basket_stats = {}
    
    for arm in arms:
        conv_spend = df[(df['segment'] == arm) & (df['conversion'] == 1)]['spend'].values
        n_conv = len(conv_spend)
        mean_spend = np.mean(conv_spend)
        
        # Bootstrap CI for mean spend among converters
        boot_means = rng.choice(conv_spend, size=(n_boot, n_conv), replace=True).mean(axis=1)
        ci_low, ci_high = np.percentile(boot_means, [2.5, 97.5])
        
        basket_stats[arm] = {
            'n_conv': n_conv,
            'mean_spend': mean_spend,
            'ci_low': ci_low,
            'ci_high': ci_high
        }
        print(f"Arm: {arm:<15} | Converters: {n_conv:3d} | Mean Spend/Converter: ${mean_spend:.2f} (95% Boot CI: [${ci_low:.2f}, ${ci_high:.2f}])")
        
    print("\n*IMPORTANT NOTE: Spend per converter is conditioned on conversion (a post-treatment variable) and is NOT a causal estimate.*")
    
    # Conversion rates
    p_ctrl = df[df['segment'] == 'No E-Mail']['conversion'].mean()
    p_mens = df[df['segment'] == 'Mens E-Mail']['conversion'].mean()
    p_womens = df[df['segment'] == 'Womens E-Mail']['conversion'].mean()
    
    s_ctrl = basket_stats['No E-Mail']['mean_spend']
    s_mens = basket_stats['Mens E-Mail']['mean_spend']
    s_womens = basket_stats['Womens E-Mail']['mean_spend']
    
    print(f"\nBase Numbers:")
    print(f"  Control: Conv Rate = {p_ctrl:.6f} ({p_ctrl*100:.4f}%), Mean Spend/Conv = ${s_ctrl:.4f}")
    print(f"  Mens:    Conv Rate = {p_mens:.6f} ({p_mens*100:.4f}%), Mean Spend/Conv = ${s_mens:.4f}")
    print(f"  Womens:  Conv Rate = {p_womens:.6f} ({p_womens*100:.4f}%), Mean Spend/Conv = ${s_womens:.4f}")
    
    # Decompositions:
    # Total ATE = P_T * S_T - P_C * S_C
    # Extensive = (P_T - P_C) * S_C
    # Intensive = P_T * (S_T - S_C)
    
    decomp_records = []
    for trt_name, p_t, s_t in [('Mens E-Mail vs No E-Mail', p_mens, s_mens), ('Womens E-Mail vs No E-Mail', p_womens, s_womens)]:
        ate_spend_calc = (p_t * s_t) - (p_ctrl * s_ctrl)
        ext_margin = (p_t - p_ctrl) * s_ctrl
        int_margin = p_t * (s_t - s_ctrl)
        sum_margins = ext_margin + int_margin
        
        ext_pct = (ext_margin / ate_spend_calc) * 100
        int_pct = (int_margin / ate_spend_calc) * 100
        
        decomp_records.append({
            'Comparison': trt_name,
            'Total Spend ATE ($)': ate_spend_calc,
            'Extensive Margin ($)': ext_margin,
            'Extensive Share (%)': ext_pct,
            'Intensive Margin ($)': int_margin,
            'Intensive Share (%)': int_pct,
            'Sum (Ext + Int) ($)': sum_margins,
            'Difference from Total': abs(sum_margins - ate_spend_calc)
        })
        
    decomp_df = pd.DataFrame(decomp_records)
    print("\nSpend ATE Exact Decomposition (Descriptive Arithmetic):")
    print(decomp_df.to_string(index=False))

if __name__ == '__main__':
    main()
