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
from sklearn.model_selection import KFold
from collections import Counter

def main():
    df = pd.read_csv('hillstrom_cleaned.csv')
    
    # Define purchase history groups
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

    # -------------------------------------------------------------
    # 1. Update subgroup_estimates.csv and 9 Head-to-Head Tests
    # -------------------------------------------------------------
    sub_df = pd.read_csv('subgroup_estimates.csv')
    is_rate = sub_df['Outcome'].isin(['visit', 'conversion'])
    rate_cols = [
        'Mean_Control', 'Mean_Mens', 'Mean_Womens',
        'ATE_Mens_vs_Ctrl', 'SE_Mens_vs_Ctrl', 'CI_Low_Mens_vs_Ctrl', 'CI_High_Mens_vs_Ctrl',
        'ATE_Womens_vs_Ctrl', 'SE_Womens_vs_Ctrl', 'CI_Low_Womens_vs_Ctrl', 'CI_High_Womens_vs_Ctrl',
        'ATE_Mens_vs_Womens', 'SE_Mens_vs_Womens', 'CI_Low_Mens_vs_Womens', 'CI_High_Mens_vs_Womens'
    ]
    # Check if already in percentage points or decimals
    # If max of Mean_Control for visit is < 1.0, it is in decimals
    if sub_df.loc[sub_df['Outcome'] == 'visit', 'Mean_Control'].max() < 1.0:
        for c in rate_cols:
            sub_df.loc[is_rate, c] = sub_df.loc[is_rate, c] * 100.0
            
    # Add units column for crystal clarity
    sub_df['Metric_Unit'] = np.where(is_rate, 'percentage points (pp)', 'dollars ($)')
    sub_df.to_csv('subgroup_estimates.csv', index=False)
    print("Re-saved 'subgroup_estimates.csv' with explicit percentage points and dollars.")

    # 9 Head-to-Head Tests with Holm Correction
    h2h_df = sub_df[sub_df['Modifier'] == 'purchase_history'][
        ['Subgroup', 'Outcome', 'ATE_Mens_vs_Womens', 'CI_Low_Mens_vs_Womens', 'CI_High_Mens_vs_Womens', 'P_Mens_vs_Womens', 'Metric_Unit']
    ].copy()
    h2h_df = h2h_df.sort_values('P_Mens_vs_Womens').reset_index(drop=True)
    m = len(h2h_df)
    adj_p = []
    for i, row in h2h_df.iterrows():
        k = i + 1
        adj_p.append((m - k + 1) * row['P_Mens_vs_Womens'])
    for i in range(1, m):
        adj_p[i] = max(adj_p[i], adj_p[i-1])
    h2h_df['Holm_p'] = [min(1.0, p) for p in adj_p]
    h2h_df['Conclusion'] = np.where(h2h_df['Holm_p'] < 0.05, 'Confirmed (survives Holm)', 'Exploratory (does not survive)')

    print("\n" + "="*90)
    print("1. 9 HEAD-TO-HEAD TESTS ACROSS PURCHASE-HISTORY GROUPS (HOLM CORRECTION)")
    print("="*90)
    print(h2h_df[['Subgroup', 'Outcome', 'ATE_Mens_vs_Womens', 'CI_Low_Mens_vs_Womens', 'CI_High_Mens_vs_Womens', 'Metric_Unit', 'P_Mens_vs_Womens', 'Holm_p', 'Conclusion']].to_string(index=False))

    # -------------------------------------------------------------
    # 2 & 3. Break-Even Analysis for Mens and Womens E-Mail
    # -------------------------------------------------------------
    # ATE Spend and Lower Bound Bootstrap CI from step 1
    # Mens vs Ctrl: ATE = 0.769827, Lower Bound = 0.4875
    # Womens vs Ctrl: ATE = 0.424412, Lower Bound = 0.1689
    ate_spend_m = 0.769827
    boot_low_m = 0.4875
    ate_spend_w = 0.424412
    boot_low_w = 0.1689

    margins = [0.20, 0.40, 0.60, 0.80, 1.00]
    be_rows = []
    for m_val in margins:
        be_m_point = ate_spend_m * m_val
        be_m_cons = boot_low_m * m_val
        be_w_point = ate_spend_w * m_val
        be_w_cons = boot_low_w * m_val
        be_rows.append({
            'Gross Margin (%)': f"{int(m_val*100)}%",
            'Mens Break-Even Cost (Point)': f"${be_m_point:.4f}",
            'Mens Break-Even Cost (Conservative 95% Low)': f"${be_m_cons:.4f}",
            'Womens Break-Even Cost (Point)': f"${be_w_point:.4f}",
            'Womens Break-Even Cost (Conservative 95% Low)': f"${be_w_cons:.4f}"
        })
    be_df = pd.DataFrame(be_rows)
    print("\n" + "="*90)
    print("3. BREAK-EVEN COST PER EMAIL (POINT ESTIMATE VS CONSERVATIVE LOWER CI)")
    print("="*90)
    print(be_df.to_string(index=False))

    # Produce Break-Even Chart
    costs = np.linspace(0.0, 0.45, 100)
    display_margin = 0.40
    
    # Incremental profit per 1,000 emails: 1000 * (ATE * margin - cost)
    prof_m_point = 1000 * (ate_spend_m * display_margin - costs)
    prof_m_low = 1000 * (boot_low_m * display_margin - costs)
    prof_m_high = 1000 * (1.0589 * display_margin - costs)
    
    prof_w_point = 1000 * (ate_spend_w * display_margin - costs)
    prof_w_low = 1000 * (boot_low_w * display_margin - costs)
    prof_w_high = 1000 * (0.6821 * display_margin - costs)
    
    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=300)
    
    ax.plot(costs, prof_m_point, color='#1f77b4', linewidth=2.2, label=f'Mens E-Mail (Point ATE = ${ate_spend_m:.2f})')
    ax.fill_between(costs, prof_m_low, prof_m_high, color='#1f77b4', alpha=0.18, label='Mens E-Mail 95% Bootstrap Band')
    
    ax.plot(costs, prof_w_point, color='#ff7f0e', linewidth=2.2, label=f'Womens E-Mail (Point ATE = ${ate_spend_w:.2f})')
    ax.fill_between(costs, prof_w_low, prof_w_high, color='#ff7f0e', alpha=0.18, label='Womens E-Mail 95% Bootstrap Band')
    
    # Break-even zero line
    ax.axhline(0, color='black', linestyle='-', linewidth=1.0, alpha=0.8)
    
    # Illustrative default cost ($0.05)
    ax.axvline(0.05, color='#d62728', linestyle=':', linewidth=1.5, label='Illustrative Default Cost ($0.05 / email)')
    
    # Break-even point markers
    be_cost_m = ate_spend_m * display_margin
    be_cost_w = ate_spend_w * display_margin
    ax.scatter([be_cost_m], [0], color='#1f77b4', s=70, zorder=5)
    ax.annotate(f'Mens Break-Even:\n${be_cost_m:.3f} / email', xy=(be_cost_m, 0), xytext=(be_cost_m + 0.02, 60),
                arrowprops=dict(arrowstyle='->', color='#1f77b4', lw=1.2), fontsize=9.5, fontweight='bold', color='#1f77b4')
    
    ax.scatter([be_cost_w], [0], color='#ff7f0e', s=70, zorder=5)
    ax.annotate(f'Womens Break-Even:\n${be_cost_w:.3f} / email', xy=(be_cost_w, 0), xytext=(be_cost_w - 0.10, -90),
                arrowprops=dict(arrowstyle='->', color='#ff7f0e', lw=1.2), fontsize=9.5, fontweight='bold', color='#ff7f0e')
    
    ax.set_xlabel('Cost per Email Dispatched ($)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Incremental Gross Profit per 1,000 Emails ($)', fontsize=11, fontweight='bold')
    ax.set_title(f'Incremental Profit vs. Email Dispatch Cost (Gross Margin = {int(display_margin*100)}%)', fontsize=13, fontweight='bold', pad=12)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper right', frameon=True, framealpha=0.92, fontsize=9.5)
    
    plt.tight_layout()
    fig.savefig('profit_breakeven_chart.png', dpi=300)
    plt.close()
    print("Saved 'profit_breakeven_chart.png'.")

    # -------------------------------------------------------------
    # 4. Strategy Comparison & Sensitivity Table
    # -------------------------------------------------------------
    # Illustrative defaults: margin = 0.40, cost = 0.05
    # (a) No email: $0.00
    # (b) Womens E-Mail to everyone: 1000 * (0.424412 * 0.40 - 0.05)
    # (c) Mens E-Mail to everyone: 1000 * (0.769827 * 0.40 - 0.05)
    # (d) In-sample purchase-history rule
    def calc_strategy_profit(margin_val, cost_val):
        prof_a = 0.0
        prof_b = 1000.0 * (ate_spend_w * margin_val - cost_val)
        prof_c = 1000.0 * (ate_spend_m * margin_val - cost_val)
        
        # Subgroup ATEs for (d)
        # Mens-only (45.03%): Mens ATE = 0.6888, Womens ATE = 0.2844
        # Womens-only (44.90%): Mens ATE = 0.6277, Womens ATE = 0.6436
        # Both (10.08%): Mens ATE = 1.8217, Womens ATE = 0.1586
        ate_m_mo = 0.688849
        ate_w_mo = 0.284400
        ate_m_wo = 0.627749
        ate_w_wo = 0.643666
        ate_m_b = 1.821703
        ate_w_b = 0.158598
        
        w_mo = 28818 / 64000
        w_wo = 28734 / 64000
        w_b = 6448 / 64000
        
        best_mo = max(ate_m_mo * margin_val - cost_val, ate_w_mo * margin_val - cost_val, 0.0)
        best_wo = max(ate_m_wo * margin_val - cost_val, ate_w_wo * margin_val - cost_val, 0.0)
        best_b = max(ate_m_b * margin_val - cost_val, ate_w_b * margin_val - cost_val, 0.0)
        
        prof_d = 1000.0 * (w_mo * best_mo + w_wo * best_wo + w_b * best_b)
        
        return prof_a, prof_b, prof_c, prof_d

    pa_def, pb_def, pc_def, pd_def = calc_strategy_profit(0.40, 0.05)
    print("\n" + "="*90)
    print("4. STRATEGY COMPARISON AT ILLUSTRATIVE DEFAULTS (MARGIN = 40%, COST = $0.05)")
    print("="*90)
    strat_df = pd.DataFrame([
        {'Strategy': '(a) No E-Mail', 'Incremental Profit per 1k ($)': f"${pa_def:.2f}", 'Lift over Mens All ($)': f"${pa_def - pc_def:.2f}"},
        {'Strategy': '(b) Womens E-Mail to Everyone', 'Incremental Profit per 1k ($)': f"${pb_def:.2f}", 'Lift over Mens All ($)': f"${pb_def - pc_def:.2f}"},
        {'Strategy': '(c) Mens E-Mail to Everyone', 'Incremental Profit per 1k ($)': f"${pc_def:.2f}", 'Lift over Mens All ($)': f"$0.00"},
        {'Strategy': '(d) Purchase-History Rule (In-Sample)', 'Incremental Profit per 1k ($)': f"${pd_def:.2f}", 'Lift over Mens All ($)': f"${pd_def - pc_def:+.2f}"}
    ])
    print(strat_df.to_string(index=False))

    # Sensitivity Table over margins and costs
    grid_margins = [0.20, 0.40, 0.60]
    grid_costs = [0.01, 0.03, 0.05, 0.10, 0.20]
    
    sens_rows = []
    for g_m in grid_margins:
        for g_c in grid_costs:
            p_a, p_b, p_c, p_d = calc_strategy_profit(g_m, g_c)
            sens_rows.append({
                'Gross Margin': f"{int(g_m*100)}%",
                'Cost / Email': f"${g_c:.2f}",
                'No Email ($)': f"${p_a:.2f}",
                'Womens All ($)': f"${p_b:.2f}",
                'Mens All ($)': f"${p_c:.2f}",
                'Purchase-History Rule ($)': f"${p_d:.2f}",
                'Rule vs Mens All ($)': f"${p_d - p_c:+.2f}"
            })
    sens_df = pd.DataFrame(sens_rows)
    print("\nSensitivity Matrix: Strategy Profit per 1,000 Customers Across Cost & Margin Grids:")
    print(sens_df.to_string(index=False))

    # -------------------------------------------------------------
    # 5. Honest Cross-Fitting Evaluation of Policy (d)
    # -------------------------------------------------------------
    print("\n" + "="*90)
    print("5. HONEST EVALUATION OF POLICY (D): 5-FOLD CROSS-FITTING (20 REPEATS, SEED=42)")
    print("="*90)
    
    groups = ['Mens-only', 'Womens-only', 'Both']
    def eval_cross_fitting(margin_val, cost_val, n_repeats=20, base_seed=42):
        policy_d_repeats = []
        policy_c_repeats = []
        rule_choices_log = []
        
        for r in range(n_repeats):
            kf = KFold(n_splits=5, shuffle=True, random_state=base_seed + r)
            fold_d_vals = []
            fold_c_vals = []
            
            for train_idx, test_idx in kf.split(df):
                tr = df.iloc[train_idx]
                te = df.iloc[test_idx]
                n_te_total = len(te)
                
                # Fit policy on 4 folds
                fold_rule = {}
                for g in groups:
                    sub_tr = tr[tr['purchase_history'] == g]
                    m_ctrl = sub_tr[sub_tr['segment'] == 'No E-Mail']['spend'].mean()
                    m_mens = sub_tr[sub_tr['segment'] == 'Mens E-Mail']['spend'].mean()
                    m_womens = sub_tr[sub_tr['segment'] == 'Womens E-Mail']['spend'].mean()
                    
                    prof_m = (m_mens - m_ctrl) * margin_val - cost_val
                    prof_w = (m_womens - m_ctrl) * margin_val - cost_val
                    prof_0 = 0.0
                    
                    best_arm = max([('Mens E-Mail', prof_m), ('Womens E-Mail', prof_w), ('No E-Mail', prof_0)], key=lambda x: x[1])[0]
                    fold_rule[g] = best_arm
                    
                rule_choices_log.append(fold_rule)
                
                # Evaluate on test fold
                te_prof_d = 0.0
                te_prof_c = 0.0
                
                for g in groups:
                    sub_te = te[te['purchase_history'] == g]
                    n_g = len(sub_te)
                    
                    m_te_ctrl = sub_te[sub_te['segment'] == 'No E-Mail']['spend'].mean()
                    m_te_mens = sub_te[sub_te['segment'] == 'Mens E-Mail']['spend'].mean()
                    m_te_womens = sub_te[sub_te['segment'] == 'Womens E-Mail']['spend'].mean()
                    
                    # Policy d
                    arm_d = fold_rule[g]
                    if arm_d == 'Mens E-Mail':
                        g_prof_d = (m_te_mens - m_te_ctrl) * margin_val - cost_val
                    elif arm_d == 'Womens E-Mail':
                        g_prof_d = (m_te_womens - m_te_ctrl) * margin_val - cost_val
                    else:
                        g_prof_d = 0.0
                        
                    te_prof_d += (n_g / n_te_total) * g_prof_d
                    
                    # Policy c (Mens to everyone)
                    g_prof_c = (m_te_mens - m_te_ctrl) * margin_val - cost_val
                    te_prof_c += (n_g / n_te_total) * g_prof_c
                    
                fold_d_vals.append(te_prof_d * 1000.0)
                fold_c_vals.append(te_prof_c * 1000.0)
                
            policy_d_repeats.append(np.mean(fold_d_vals))
            policy_c_repeats.append(np.mean(fold_c_vals))
            
        return np.array(policy_d_repeats), np.array(policy_c_repeats), rule_choices_log

    d_vals, c_vals, rule_log = eval_cross_fitting(0.40, 0.05, n_repeats=20, base_seed=42)
    diff_d_c = d_vals - c_vals
    
    # Bootstrap CI for mean policy value across 10,000 resamples of the 20 splits
    rng = np.random.default_rng(42)
    boot_d = rng.choice(d_vals, size=(10000, len(d_vals)), replace=True).mean(axis=1)
    ci_d_low, ci_d_high = np.percentile(boot_d, [2.5, 97.5])
    
    boot_c = rng.choice(c_vals, size=(10000, len(c_vals)), replace=True).mean(axis=1)
    ci_c_low, ci_c_high = np.percentile(boot_c, [2.5, 97.5])
    
    boot_diff = rng.choice(diff_d_c, size=(10000, len(diff_d_c)), replace=True).mean(axis=1)
    ci_diff_low, ci_diff_high = np.percentile(boot_diff, [2.5, 97.5])

    print(f"Policy (d) Out-of-Sample Mean Value:  ${np.mean(d_vals):.2f} / 1k (95% Boot CI: [${ci_d_low:.2f}, ${ci_d_high:.2f}])")
    print(f"Policy (c) 'Mens All' Mean Value:      ${np.mean(c_vals):.2f} / 1k (95% Boot CI: [${ci_c_low:.2f}, ${ci_c_high:.2f}])")
    print(f"Incremental Value (Policy d - Policy c): ${np.mean(diff_d_c):.2f} / 1k (95% Boot CI: [${ci_diff_low:.2f}, ${ci_diff_high:.2f}])")
    
    print("\nDistribution of Policy Decisions across all 100 cross-validation folds (20 splits x 5 folds):")
    for g in groups:
        counts = Counter([r[g] for r in rule_log])
        print(f"  {g:<15}: {dict(counts)}")

if __name__ == '__main__':
    main()
