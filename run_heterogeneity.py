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
import statsmodels.api as sm
from scipy import stats

def main():
    df = pd.read_csv('hillstrom_cleaned.csv')
    
    # -------------------------------------------------------------
    # 0. R-Squared of previous Lin (2013) models
    # -------------------------------------------------------------
    cov_num = ['recency', 'history']
    cov_bin = ['mens', 'womens', 'newbie']
    zip_dummies = pd.get_dummies(df['zip_code'], prefix='zip', drop_first=True, dtype=float)
    chan_dummies = pd.get_dummies(df['channel'], prefix='chan', drop_first=True, dtype=float)
    X_raw = pd.concat([df[cov_num + cov_bin], zip_dummies, chan_dummies], axis=1)
    X_centered = X_raw - X_raw.mean(axis=0)

    T_mens = (df['segment'] == 'Mens E-Mail').astype(float)
    T_womens = (df['segment'] == 'Womens E-Mail').astype(float)
    inter_mens = X_centered.multiply(T_mens, axis=0)
    inter_mens.columns = [f"{c}_x_mens" for c in inter_mens.columns]
    inter_womens = X_centered.multiply(T_womens, axis=0)
    inter_womens.columns = [f"{c}_x_womens" for c in inter_womens.columns]

    Z_joint = pd.concat([
        pd.Series(1.0, index=df.index, name='const'),
        T_mens.rename('T_mens'),
        T_womens.rename('T_womens'),
        X_centered,
        inter_mens,
        inter_womens
    ], axis=1)

    print("="*90)
    print("0. R-SQUARED OF REGRESSION-ADJUSTED MODELS (PREVIOUS STEP)")
    print("="*90)
    r2_records = []
    for out in ['visit', 'conversion', 'spend']:
        # Joint model
        mod_j = sm.OLS(df[out], Z_joint).fit()
        
        # Separate Mens vs Control
        df_mc = df[df['segment'].isin(['No E-Mail', 'Mens E-Mail'])].copy()
        X_mc = X_raw.loc[df_mc.index]
        Xc_mc = X_mc - X_mc.mean(axis=0)
        Tm = (df_mc['segment'] == 'Mens E-Mail').astype(float)
        inter_m = Xc_mc.multiply(Tm, axis=0)
        Z_mc = pd.concat([pd.Series(1.0, index=df_mc.index, name='const'), Tm.rename('T'), Xc_mc, inter_m], axis=1)
        mod_m = sm.OLS(df_mc[out], Z_mc).fit()
        
        # Separate Womens vs Control
        df_wc = df[df['segment'].isin(['No E-Mail', 'Womens E-Mail'])].copy()
        X_wc = X_raw.loc[df_wc.index]
        Xc_wc = X_wc - X_wc.mean(axis=0)
        Tw = (df_wc['segment'] == 'Womens E-Mail').astype(float)
        inter_w = Xc_wc.multiply(Tw, axis=0)
        Z_wc = pd.concat([pd.Series(1.0, index=df_wc.index, name='const'), Tw.rename('T'), Xc_wc, inter_w], axis=1)
        mod_w = sm.OLS(df_wc[out], Z_wc).fit()
        
        r2_records.append({
            'Outcome': out,
            'Joint Lin (2013) R2': f"{mod_j.rsquared:.4f} ({mod_j.rsquared*100:.2f}%)",
            'Mens vs Control R2': f"{mod_m.rsquared:.4f} ({mod_m.rsquared*100:.2f}%)",
            'Womens vs Control R2': f"{mod_w.rsquared:.4f} ({mod_w.rsquared*100:.2f}%)"
        })
    print(pd.DataFrame(r2_records).to_string(index=False))

    # -------------------------------------------------------------
    # 1. Pre-specified Effect Modifiers
    # -------------------------------------------------------------
    print("\n" + "="*90)
    print("1. PRE-SPECIFIED EFFECT MODIFIERS & SUBGROUP COUNTS")
    print("="*90)
    
    # 1. Purchase-history group
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
    
    # 2. History quartiles: 4 bands
    # q25=64.66, q50=158.11, q75=325.66
    q25, q50, q75 = df['history'].quantile([0.25, 0.50, 0.75])
    bins_hist = [-np.inf, q25, q50, q75, np.inf]
    labels_hist = [f'1) $29.99-${q25:.2f}', f'2) ${q25:.2f}-${q50:.2f}', f'3) ${q50:.2f}-${q75:.2f}', f'4) ${q75:.2f}+']
    df['history_bracket'] = pd.cut(df['history'], bins=bins_hist, labels=labels_hist)
    
    # 3. Recency in 4 bands: 1-3, 4-6, 7-9, 10-12
    bins_rec = [0, 3, 6, 9, 12]
    labels_rec = ['1-3m', '4-6m', '7-9m', '10-12m']
    df['recency_bracket'] = pd.cut(df['recency'], bins=bins_rec, labels=labels_rec)

    modifiers = ['purchase_history', 'newbie', 'channel', 'zip_code', 'history_bracket', 'recency_bracket']
    
    for mod in modifiers:
        counts = df[mod].value_counts(dropna=False).sort_index()
        pcts = df[mod].value_counts(dropna=False, normalize=True).sort_index() * 100
        print(f"\nModifier: '{mod}' (Total N = {len(df):,})")
        for lvl, cnt in counts.items():
            flag = " [FLAG: < 500 customers]" if cnt < 500 else ""
            print(f"  Level: {str(lvl):<22} | Count: {cnt:6,d} ({pcts[lvl]:5.2f}%){flag}")
            
    # Check if 'Neither' exists
    neither_count = (df['purchase_history'] == 'Neither').sum()
    print(f"\nPurchase-History 'Neither' group count: {neither_count} [FLAG: 0 customers in dataset!]")

    # -------------------------------------------------------------
    # 2. Confirmatory Interaction Tests
    # -------------------------------------------------------------
    print("\n" + "="*90)
    print("2. CONFIRMATORY INTERACTION TESTS (JOINT WALD TEST WITH HC3)")
    print("="*90)
    outcomes = ['visit', 'conversion', 'spend']
    int_records = []
    
    for mod in modifiers:
        # Get dummies
        dummies = pd.get_dummies(df[mod], prefix=mod, drop_first=True, dtype=float)
        d_cols = dummies.columns.tolist()
        
        inter_m = dummies.multiply(T_mens, axis=0)
        inter_m.columns = [f"{c}_x_mens" for c in inter_m.columns]
        
        inter_w = dummies.multiply(T_womens, axis=0)
        inter_w.columns = [f"{c}_x_womens" for c in inter_w.columns]
        
        Z = pd.concat([
            pd.Series(1.0, index=df.index, name='const'),
            T_mens.rename('T_mens'),
            T_womens.rename('T_womens'),
            dummies,
            inter_m,
            inter_w
        ], axis=1)
        
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
            
            int_records.append({
                'Modifier': mod,
                'Outcome': out,
                'df': df_test,
                'Wald_Chi2': stat,
                'Raw_p': p_val
            })
            
    int_df = pd.DataFrame(int_records)
    
    # Apply Holm correction across all 18 tests
    int_df = int_df.sort_values('Raw_p').reset_index(drop=True)
    m = len(int_df)
    adj_p = []
    for i, row in int_df.iterrows():
        k = i + 1
        adj_p.append((m - k + 1) * row['Raw_p'])
    for i in range(1, m):
        adj_p[i] = max(adj_p[i], adj_p[i-1])
    int_df['Holm_p'] = [min(1.0, p) for p in adj_p]
    int_df['Significant_at_05'] = int_df['Holm_p'] < 0.05
    
    print(f"Total Interaction Tests Evaluated: {m} (6 modifiers x 3 outcomes)")
    print(int_df.to_string(index=False))

    # -------------------------------------------------------------
    # 3. Subgroup Estimates (Every level of every modifier)
    # -------------------------------------------------------------
    print("\n" + "="*90)
    print("3. SUBGROUP ESTIMATES & FOREST PLOT DATA GENERATION")
    print("="*90)
    
    subgroup_records = []
    
    for mod in modifiers:
        levels = df[mod].unique()
        # Sort levels nicely
        if hasattr(levels, 'sort'):
            levels = sorted(levels)
        else:
            levels = list(levels)
            
        for lvl in levels:
            sub = df[df[mod] == lvl]
            n_tot = len(sub)
            
            # Sample sizes and converters per arm
            n_ctrl = (sub['segment'] == 'No E-Mail').sum()
            n_mens = (sub['segment'] == 'Mens E-Mail').sum()
            n_womens = (sub['segment'] == 'Womens E-Mail').sum()
            
            conv_ctrl = sub[sub['segment'] == 'No E-Mail']['conversion'].sum()
            conv_mens = sub[sub['segment'] == 'Mens E-Mail']['conversion'].sum()
            conv_womens = sub[sub['segment'] == 'Womens E-Mail']['conversion'].sum()
            
            # Fit OLS on subgroup: outcome ~ 1 + T_mens + T_womens with HC3
            # We want: Mens vs Ctrl, Womens vs Ctrl, Mens vs Womens
            t_m = (sub['segment'] == 'Mens E-Mail').astype(float)
            t_w = (sub['segment'] == 'Womens E-Mail').astype(float)
            Z_sub = pd.concat([pd.Series(1.0, index=sub.index, name='const'), t_m.rename('T_mens'), t_w.rename('T_womens')], axis=1)
            
            for out in outcomes:
                y_sub = sub[out].values
                mod_sub = sm.OLS(y_sub, Z_sub).fit(cov_type='HC3')
                
                # Mens vs Ctrl
                ate_m = mod_sub.params['T_mens']
                se_m = mod_sub.bse['T_mens']
                ci_m_low, ci_m_high = ate_m - 1.95996 * se_m, ate_m + 1.95996 * se_m
                p_m = mod_sub.pvalues['T_mens']
                
                # Womens vs Ctrl
                ate_w = mod_sub.params['T_womens']
                se_w = mod_sub.bse['T_womens']
                ci_w_low, ci_w_high = ate_w - 1.95996 * se_w, ate_w + 1.95996 * se_w
                p_w = mod_sub.pvalues['T_womens']
                
                # Mens vs Womens
                contrast = np.array([0.0, 1.0, -1.0])
                tt = mod_sub.t_test(contrast)
                ate_h2h = float(tt.effect.item() if hasattr(tt.effect, 'item') else tt.effect)
                se_h2h = float(tt.sd.item() if hasattr(tt.sd, 'item') else tt.sd)
                ci_h2h_low, ci_h2h_high = ate_h2h - 1.95996 * se_h2h, ate_h2h + 1.95996 * se_h2h
                p_h2h = float(tt.pvalue.item() if hasattr(tt.pvalue, 'item') else tt.pvalue)
                
                # Arm rates / means
                mean_ctrl = sub[sub['segment'] == 'No E-Mail'][out].mean()
                mean_mens = sub[sub['segment'] == 'Mens E-Mail'][out].mean()
                mean_womens = sub[sub['segment'] == 'Womens E-Mail'][out].mean()
                
                subgroup_records.append({
                    'Modifier': mod,
                    'Subgroup': str(lvl),
                    'Outcome': out,
                    'N_Total': n_tot,
                    'N_Control': n_ctrl,
                    'N_Mens': n_mens,
                    'N_Womens': n_womens,
                    'Conv_Control': conv_ctrl,
                    'Conv_Mens': conv_mens,
                    'Conv_Womens': conv_womens,
                    'Mean_Control': mean_ctrl,
                    'Mean_Mens': mean_mens,
                    'Mean_Womens': mean_womens,
                    # Mens vs Control
                    'ATE_Mens_vs_Ctrl': ate_m,
                    'SE_Mens_vs_Ctrl': se_m,
                    'CI_Low_Mens_vs_Ctrl': ci_m_low,
                    'CI_High_Mens_vs_Ctrl': ci_m_high,
                    'P_Mens_vs_Ctrl': p_m,
                    # Womens vs Control
                    'ATE_Womens_vs_Ctrl': ate_w,
                    'SE_Womens_vs_Ctrl': se_w,
                    'CI_Low_Womens_vs_Ctrl': ci_w_low,
                    'CI_High_Womens_vs_Ctrl': ci_w_high,
                    'P_Womens_vs_Ctrl': p_w,
                    # Head to Head
                    'ATE_Mens_vs_Womens': ate_h2h,
                    'SE_Mens_vs_Womens': se_h2h,
                    'CI_Low_Mens_vs_Womens': ci_h2h_low,
                    'CI_High_Mens_vs_Womens': ci_h2h_high,
                    'P_Mens_vs_Womens': p_h2h
                })
                
    sub_df = pd.DataFrame(subgroup_records)
    sub_df.to_csv('subgroup_estimates.csv', index=False)
    print("Saved 'subgroup_estimates.csv' successfully.")
    
    # -------------------------------------------------------------
    # 4. Head-to-Head Mens vs Womens within Purchase-History Groups
    # -------------------------------------------------------------
    print("\n" + "="*90)
    print("4. HEAD-TO-HEAD: MENS VS WOMENS WITHIN PURCHASE-HISTORY GROUPS")
    print("="*90)
    h2h_ph = sub_df[(sub_df['Modifier'] == 'purchase_history')][
        ['Subgroup', 'Outcome', 'N_Total', 'Conv_Mens', 'Conv_Womens', 'Mean_Mens', 'Mean_Womens', 'ATE_Mens_vs_Womens', 'CI_Low_Mens_vs_Womens', 'CI_High_Mens_vs_Womens', 'P_Mens_vs_Womens']
    ]
    print(h2h_ph.to_string(index=False))

    # -------------------------------------------------------------
    # Produce Forest Plots (Visit and Spend)
    # -------------------------------------------------------------
    print("\n" + "="*90)
    print("GENERATING FOREST PLOTS FOR VISIT AND SPEND")
    print("="*90)
    
    # Overall ATEs as reference lines
    # From Step 1/Lin:
    overall_ate_visit_m = 0.0766
    overall_ate_visit_w = 0.0452
    overall_ate_spend_m = 0.7698
    overall_ate_spend_w = 0.4244
    
    # 1. Forest Plot for Visit
    fig, axes = plt.subplots(nrows=3, ncols=2, figsize=(16, 14), dpi=300)
    axes = axes.flatten()
    
    mod_titles = {
        'purchase_history': 'Purchase History Segment',
        'newbie': 'Newbie Customer (<12m)',
        'channel': 'Historical Shopping Channel',
        'zip_code': 'Zip Classification',
        'history_bracket': 'Historical Spend Quartiles',
        'recency_bracket': 'Recency Bands'
    }
    
    for ax_idx, mod in enumerate(modifiers):
        ax = axes[ax_idx]
        mod_data = sub_df[(sub_df['Modifier'] == mod) & (sub_df['Outcome'] == 'visit')].copy()
        
        y_pos = np.arange(len(mod_data))
        labels = mod_data['Subgroup'].tolist()
        
        # Mens vs Control points and errors
        ax.errorbar(
            mod_data['ATE_Mens_vs_Ctrl'], y_pos + 0.15,
            xerr=[mod_data['ATE_Mens_vs_Ctrl'] - mod_data['CI_Low_Mens_vs_Ctrl'], mod_data['CI_High_Mens_vs_Ctrl'] - mod_data['ATE_Mens_vs_Ctrl']],
            fmt='o', color='#1f77b4', label='Mens vs Control', capsize=3.5, elinewidth=1.5, markersize=5.5
        )
        
        # Womens vs Control points and errors
        ax.errorbar(
            mod_data['ATE_Womens_vs_Ctrl'], y_pos - 0.15,
            xerr=[mod_data['ATE_Womens_vs_Ctrl'] - mod_data['CI_Low_Womens_vs_Ctrl'], mod_data['CI_High_Womens_vs_Ctrl'] - mod_data['ATE_Womens_vs_Ctrl']],
            fmt='s', color='#ff7f0e', label='Womens vs Control', capsize=3.5, elinewidth=1.5, markersize=5.5
        )
        
        # Overall reference lines
        ax.axvline(overall_ate_visit_m, color='#1f77b4', linestyle=':', alpha=0.7, label='Overall Mens ATE (+7.66 pp)' if ax_idx==0 else "")
        ax.axvline(overall_ate_visit_w, color='#ff7f0e', linestyle=':', alpha=0.7, label='Overall Womens ATE (+4.52 pp)' if ax_idx==0 else "")
        ax.axvline(0, color='gray', linestyle='-', linewidth=0.8, alpha=0.5)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=10)
        ax.set_title(mod_titles[mod], fontsize=12, fontweight='bold', pad=8)
        ax.set_xlabel('Visit Rate Difference (ATE in pp)', fontsize=9.5)
        ax.grid(axis='x', linestyle=':', alpha=0.5)
        if ax_idx == 0:
            ax.legend(loc='upper right', frameon=True, fontsize=8.5)
            
    fig.suptitle('Forest Plot: Visit Rate Subgroup Effects Across Pre-Treatment Modifiers', fontsize=14, fontweight='bold', y=0.995)
    plt.tight_layout()
    fig.savefig('forest_plot_visit.png', dpi=300)
    plt.close()
    print("Saved 'forest_plot_visit.png'.")

    # 2. Forest Plot for Spend
    fig, axes = plt.subplots(nrows=3, ncols=2, figsize=(16, 14), dpi=300)
    axes = axes.flatten()
    
    for ax_idx, mod in enumerate(modifiers):
        ax = axes[ax_idx]
        mod_data = sub_df[(sub_df['Modifier'] == mod) & (sub_df['Outcome'] == 'spend')].copy()
        
        y_pos = np.arange(len(mod_data))
        labels = mod_data['Subgroup'].tolist()
        
        # Mens vs Control points and errors
        ax.errorbar(
            mod_data['ATE_Mens_vs_Ctrl'], y_pos + 0.15,
            xerr=[mod_data['ATE_Mens_vs_Ctrl'] - mod_data['CI_Low_Mens_vs_Ctrl'], mod_data['CI_High_Mens_vs_Ctrl'] - mod_data['ATE_Mens_vs_Ctrl']],
            fmt='o', color='#1f77b4', label='Mens vs Control', capsize=3.5, elinewidth=1.5, markersize=5.5
        )
        
        # Womens vs Control points and errors
        ax.errorbar(
            mod_data['ATE_Womens_vs_Ctrl'], y_pos - 0.15,
            xerr=[mod_data['ATE_Womens_vs_Ctrl'] - mod_data['CI_Low_Womens_vs_Ctrl'], mod_data['CI_High_Womens_vs_Ctrl'] - mod_data['ATE_Womens_vs_Ctrl']],
            fmt='s', color='#ff7f0e', label='Womens vs Control', capsize=3.5, elinewidth=1.5, markersize=5.5
        )
        
        # Overall reference lines
        ax.axvline(overall_ate_spend_m, color='#1f77b4', linestyle=':', alpha=0.7, label='Overall Mens ATE (+$0.77)' if ax_idx==0 else "")
        ax.axvline(overall_ate_spend_w, color='#ff7f0e', linestyle=':', alpha=0.7, label='Overall Womens ATE (+$0.42)' if ax_idx==0 else "")
        ax.axvline(0, color='gray', linestyle='-', linewidth=0.8, alpha=0.5)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=10)
        ax.set_title(mod_titles[mod], fontsize=12, fontweight='bold', pad=8)
        ax.set_xlabel('Spend Difference (ATE in $ per customer)', fontsize=9.5)
        ax.grid(axis='x', linestyle=':', alpha=0.5)
        if ax_idx == 0:
            ax.legend(loc='upper right', frameon=True, fontsize=8.5)
            
    fig.suptitle('Forest Plot: Spend Subgroup Effects Across Pre-Treatment Modifiers', fontsize=14, fontweight='bold', y=0.995)
    plt.tight_layout()
    fig.savefig('forest_plot_spend.png', dpi=300)
    plt.close()
    print("Saved 'forest_plot_spend.png'.")

if __name__ == '__main__':
    main()
