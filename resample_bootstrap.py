import pandas as pd
import numpy as np
from sklearn.model_selection import KFold
import time

def main():
    df = pd.read_csv('hillstrom_cleaned.csv')
    
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
    
    groups = ['Mens-only', 'Womens-only', 'Both']
    params = [
        (0.40, 0.05),
        (0.40, 0.20),
        (0.20, 0.10),
        (0.20, 0.20)
    ]
    
    print("=" * 80)
    print("IN-SAMPLE POLICY (D) VS POLICY (C) FOR THE 4 PARAMETER PAIRS")
    print("=" * 80)
    
    in_sample_results = {}
    for m, c in params:
        prof_d_total = 0.0
        prof_c_total = 0.0
        decisions = {}
        for g in groups:
            sub = df[df['purchase_history'] == g]
            w_g = len(sub) / len(df)
            m_ctrl = sub[sub['segment'] == 'No E-Mail']['spend'].mean()
            m_mens = sub[sub['segment'] == 'Mens E-Mail']['spend'].mean()
            m_womens = sub[sub['segment'] == 'Womens E-Mail']['spend'].mean()
            
            p_m = (m_mens - m_ctrl) * m - c
            p_w = (m_womens - m_ctrl) * m - c
            p_0 = 0.0
            
            best_arm, best_p = max([('Mens E-Mail', p_m), ('Womens E-Mail', p_w), ('No E-Mail', p_0)], key=lambda x: x[1])
            decisions[g] = best_arm
            prof_d_total += w_g * best_p * 1000
            prof_c_total += w_g * p_m * 1000
            
        diff_dc = prof_d_total - prof_c_total
        in_sample_results[(m, c)] = {
            'decisions': decisions,
            'prof_d': prof_d_total,
            'prof_c': prof_c_total,
            'diff': diff_dc
        }
        print(f"Margin: {m:.2f}, Cost: ${c:.2f} -> In-Sample (d - c): ${diff_dc:+.2f} / 1k | Rules: {decisions}")

    print("\n" + "=" * 80)
    print("RUNNING CUSTOMER-LEVEL STRATIFIED BOOTSTRAP (200 RESAMPLES, SEED=42)")
    print("=" * 80)
    
    # Pre-index customers by arm to make stratified sampling fast
    ctrl_indices = df[df['segment'] == 'No E-Mail'].index.to_numpy()
    mens_indices = df[df['segment'] == 'Mens E-Mail'].index.to_numpy()
    womens_indices = df[df['segment'] == 'Womens E-Mail'].index.to_numpy()
    
    n_ctrl = len(ctrl_indices)
    n_mens = len(mens_indices)
    n_womens = len(womens_indices)
    
    # Store bootstrap differences for each param pair:
    # list of diffs across 200 resamples
    boot_diffs = {p: [] for p in params}
    # Track how often 'No E-Mail' was chosen for each group across the 200 resamples (or across folds)
    # The prompt says: "how often (in % of bootstrap resamples) the rule chose 'No E-Mail' for each group"
    # In each resample, a rule is chosen per fold (5 folds). We can track the percentage of folds or resamples.
    no_email_counts = {p: {g: 0 for g in groups} for p in params}
    total_decision_opportunities = 0
    
    rng = np.random.default_rng(42)
    t0 = time.time()
    
    # 200 bootstrap iterations
    N_BOOT = 200
    
    # We will track both fold-level and resample-level No E-Mail selection
    # For resample level: did the majority of folds or at least one fold choose No E-Mail, or average fold frequency?
    # Let's track total fold occurrences / (200 * 5) and resample occurrences.
    no_email_fold_counts = {p: {g: 0 for g in groups} for p in params}
    no_email_resample_counts = {p: {g: 0 for g in groups} for p in params}
    
    for b in range(N_BOOT):
        # Stratified resample
        boot_idx = np.concatenate([
            rng.choice(ctrl_indices, size=n_ctrl, replace=True),
            rng.choice(mens_indices, size=n_mens, replace=True),
            rng.choice(womens_indices, size=n_womens, replace=True)
        ])
        
        b_df = df.iloc[boot_idx].reset_index(drop=True)
        
        # 5-fold CV on this bootstrap sample
        kf = KFold(n_splits=5, shuffle=True, random_state=42 + b)
        
        # For each parameter pair, collect the 5 fold differences
        fold_diffs = {p: [] for p in params}
        resample_chose_no_email = {p: {g: False for g in groups} for p in params}
        
        for train_idx, test_idx in kf.split(b_df):
            tr = b_df.iloc[train_idx]
            te = b_df.iloc[test_idx]
            n_te = len(te)
            
            # Precompute subgroup means on train and test
            tr_stats = {}
            te_stats = {}
            for g in groups:
                sub_tr = tr[tr['purchase_history'] == g]
                tr_stats[g] = {
                    'ctrl': sub_tr[sub_tr['segment'] == 'No E-Mail']['spend'].mean(),
                    'mens': sub_tr[sub_tr['segment'] == 'Mens E-Mail']['spend'].mean(),
                    'womens': sub_tr[sub_tr['segment'] == 'Womens E-Mail']['spend'].mean()
                }
                sub_te = te[te['purchase_history'] == g]
                te_stats[g] = {
                    'w': len(sub_te) / n_te,
                    'ctrl': sub_te[sub_te['segment'] == 'No E-Mail']['spend'].mean(),
                    'mens': sub_te[sub_te['segment'] == 'Mens E-Mail']['spend'].mean(),
                    'womens': sub_te[sub_te['segment'] == 'Womens E-Mail']['spend'].mean()
                }
                
            for p in params:
                m_val, c_val = p
                fold_diff = 0.0
                
                for g in groups:
                    # Training profits
                    p_m_tr = (tr_stats[g]['mens'] - tr_stats[g]['ctrl']) * m_val - c_val
                    p_w_tr = (tr_stats[g]['womens'] - tr_stats[g]['ctrl']) * m_val - c_val
                    p_0_tr = 0.0
                    
                    # Tie-breaking: Mens E-Mail preferred if tied with Womens
                    if p_m_tr >= p_w_tr and p_m_tr >= p_0_tr:
                        arm_d = 'Mens E-Mail'
                    elif p_w_tr > p_m_tr and p_w_tr >= p_0_tr:
                        arm_d = 'Womens E-Mail'
                    else:
                        arm_d = 'No E-Mail'
                        
                    if arm_d == 'No E-Mail':
                        no_email_fold_counts[p][g] += 1
                        resample_chose_no_email[p][g] = True
                        
                    # Test fold evaluation
                    w_g_te = te_stats[g]['w']
                    p_m_te = (te_stats[g]['mens'] - te_stats[g]['ctrl']) * m_val - c_val
                    p_w_te = (te_stats[g]['womens'] - te_stats[g]['ctrl']) * m_val - c_val
                    p_0_te = 0.0
                    
                    if arm_d == 'Mens E-Mail':
                        prof_d_g = p_m_te
                    elif arm_d == 'Womens E-Mail':
                        prof_d_g = p_w_te
                    else:
                        prof_d_g = p_0_te
                        
                    prof_c_g = p_m_te
                    
                    fold_diff += w_g_te * (prof_d_g - prof_c_g)
                    
                fold_diffs[p].append(fold_diff * 1000.0)
                
        for p in params:
            boot_diffs[p].append(np.mean(fold_diffs[p]))
            for g in groups:
                if resample_chose_no_email[p][g]:
                    no_email_resample_counts[p][g] += 1

    t_end = time.time()
    print(f"Completed 200 bootstrap iterations in {t_end - t0:.2f} seconds.\n")
    
    print("=" * 95)
    print(f"{'Parameter Pair':<22} | {'In-Sample':<11} | {'Boot Mean':<11} | {'95% Percentile CI':<22} | {'Contains 0?':<11} | {'Contains In-Sample?'}")
    print("=" * 95)
    
    for p in params:
        m_val, c_val = p
        diffs = np.array(boot_diffs[p])
        boot_mean = np.mean(diffs)
        ci_low, ci_high = np.percentile(diffs, [2.5, 97.5])
        in_s = in_sample_results[p]['diff']
        contains_zero = (ci_low <= 0 <= ci_high)
        contains_in_s = (ci_low <= in_s <= ci_high)
        
        param_label = f"m={m_val:.2f}, c=${c_val:.2f}"
        print(f"{param_label:<22} | ${in_s:+8.2f}  | ${boot_mean:+8.2f}  | [${ci_low:7.2f}, ${ci_high:7.2f}] | {str(contains_zero):<11} | {str(contains_in_s)}")

    print("\n" + "=" * 95)
    print("FREQUENCY OF 'NO E-MAIL' SELECTION (% of bootstrap resamples / % of folds)")
    print("=" * 95)
    for p in params:
        m_val, c_val = p
        param_label = f"m={m_val:.2f}, c=${c_val:.2f}"
        print(f"Parameter: {param_label}")
        for g in groups:
            pct_resample = (no_email_resample_counts[p][g] / N_BOOT) * 100
            pct_folds = (no_email_fold_counts[p][g] / (N_BOOT * 5)) * 100
            print(f"  {g:<15}: {pct_resample:5.1f}% of resamples ({pct_folds:5.1f}% of folds)")

if __name__ == '__main__':
    main()
