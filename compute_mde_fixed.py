import numpy as np
import pandas as pd
from scipy import stats
import json

def run_all():
    df = pd.read_csv('hillstrom_cleaned.csv')
    
    # -------------------------------------------------------------------------
    # Helper definitions
    # -------------------------------------------------------------------------
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

    # =========================================================================
    # ITEM 1: Fixed-rule policy comparison (e) vs (c)
    # =========================================================================
    print("=" * 80)
    print("ITEM 1: FIXED-RULE POLICY COMPARISON: Policy (e) vs Policy (c)")
    print("=" * 80)
    
    w_only = df[df['purchase_history'] == 'Womens-only']
    share_wo = len(w_only) / len(df)
    
    spend_w_wo = w_only[w_only['segment'] == 'Womens E-Mail']['spend'].values
    spend_m_wo = w_only[w_only['segment'] == 'Mens E-Mail']['spend'].values
    spend_c_wo = w_only[w_only['segment'] == 'No E-Mail']['spend'].values
    
    ate_w_wo = np.mean(spend_w_wo) - np.mean(spend_c_wo)
    ate_m_wo = np.mean(spend_m_wo) - np.mean(spend_c_wo)
    ate_diff_wo = np.mean(spend_w_wo) - np.mean(spend_m_wo) # Control cancels!
    
    margins = [0.20, 0.40, 0.60, 0.80, 1.00]
    
    # Bootstrap within Womens-only stratified by arm (10,000 resamples, seed 42)
    rng = np.random.default_rng(42)
    N_BOOT = 10000
    n_w = len(spend_w_wo)
    n_m = len(spend_m_wo)
    
    # Resample means
    boot_w_means = rng.choice(spend_w_wo, size=(N_BOOT, n_w), replace=True).mean(axis=1)
    boot_m_means = rng.choice(spend_m_wo, size=(N_BOOT, n_m), replace=True).mean(axis=1)
    boot_diffs_wo = boot_w_means - boot_m_means
    
    fixed_rule_results = []
    print(f"Share of Womens-only customers: {share_wo:.6f} ({share_wo*100:.2f}%)")
    print(f"Womens-only Womens spend mean: ${np.mean(spend_w_wo):.4f}")
    print(f"Womens-only Mens spend mean:   ${np.mean(spend_m_wo):.4f}")
    print(f"Difference (Womens - Mens):    ${ate_diff_wo:+.4f}\n")
    
    for m in margins:
        point_est = 1000.0 * share_wo * m * ate_diff_wo
        boot_vals = 1000.0 * share_wo * m * boot_diffs_wo
        ci_low, ci_high = np.percentile(boot_vals, [2.5, 97.5])
        contains_zero = (ci_low <= 0 <= ci_high)
        
        fixed_rule_results.append({
            'gross_margin': m,
            'margin_pct': f"{int(m*100)}%",
            'estimate_per_1k': point_est,
            'ci_low': ci_low,
            'ci_high': ci_high,
            'contains_zero': contains_zero
        })
        print(f"Margin {int(m*100):3d}%: (e) - (c) = ${point_est:+7.2f} / 1k | 95% CI: [${ci_low:6.2f}, ${ci_high:6.2f}] | Contains 0: {contains_zero}")

    # =========================================================================
    # ITEM 3: Minimum Detectable Effect (MDE) Table
    # =========================================================================
    print("\n" + "=" * 80)
    print("ITEM 3: MINIMUM DETECTABLE EFFECT (MDE) TABLE (Power=80%, Alpha=0.05)")
    print("=" * 80)
    # Formula: MDE = (z_{0.975} + z_{0.80}) * SE = (1.95996 + 0.84162) * SE = 2.80158 * SE
    crit_mde = 1.959964 + 0.841621 # 2.801585
    
    # We need:
    # 1. Mens vs Control overall
    # 2. Womens vs Control overall
    # 3. Mens vs Womens overall
    # 4. Mens vs Womens within Womens-only
    # 5. Mens vs Womens within Both
    
    ctrl_all = df[df['segment'] == 'No E-Mail']
    mens_all = df[df['segment'] == 'Mens E-Mail']
    womens_all = df[df['segment'] == 'Womens E-Mail']
    
    both_df = df[df['purchase_history'] == 'Both']
    ctrl_both = both_df[both_df['segment'] == 'No E-Mail']
    mens_both = both_df[both_df['segment'] == 'Mens E-Mail']
    womens_both = both_df[both_df['segment'] == 'Womens E-Mail']
    
    ctrl_wo = w_only[w_only['segment'] == 'No E-Mail']
    mens_wo = w_only[w_only['segment'] == 'Mens E-Mail']
    womens_wo = w_only[w_only['segment'] == 'Womens E-Mail']
    
    mde_configs = [
        {
            'comparison': 'Mens E-Mail vs No E-Mail',
            'scope': 'Overall',
            'n1': len(mens_all), 'n2': len(ctrl_all),
            'ref_df': ctrl_all,
            'g1_df': mens_all, 'g2_df': ctrl_all
        },
        {
            'comparison': 'Womens E-Mail vs No E-Mail',
            'scope': 'Overall',
            'n1': len(womens_all), 'n2': len(ctrl_all),
            'ref_df': ctrl_all,
            'g1_df': womens_all, 'g2_df': ctrl_all
        },
        {
            'comparison': 'Mens E-Mail vs Womens E-Mail',
            'scope': 'Overall',
            'n1': len(mens_all), 'n2': len(womens_all),
            'ref_df': ctrl_all,
            'g1_df': mens_all, 'g2_df': womens_all
        },
        {
            'comparison': 'Mens E-Mail vs Womens E-Mail',
            'scope': 'Womens-only',
            'n1': len(mens_wo), 'n2': len(womens_wo),
            'ref_df': ctrl_wo,
            'g1_df': mens_wo, 'g2_df': womens_wo
        },
        {
            'comparison': 'Mens E-Mail vs Womens E-Mail',
            'scope': 'Both',
            'n1': len(mens_both), 'n2': len(womens_both),
            'ref_df': ctrl_both,
            'g1_df': mens_both, 'g2_df': womens_both
        }
    ]
    
    mde_rows = []
    for cfg in mde_configs:
        ref = cfg['ref_df']
        g1 = cfg['g1_df']
        g2 = cfg['g2_df']
        n1 = cfg['n1']
        n2 = cfg['n2']
        
        # Outcomes: visit, conversion, spend
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
                pct_of_ctrl = (mde_val / ctrl_mean) * 100.0
                comp_to_obs = f"Observed={obs_disp:+.2f}pp vs MDE={mde_disp:.2f}pp"
            else:
                s0 = ref[out].std(ddof=1)
                se = s0 * np.sqrt(1/n1 + 1/n2)
                mde_val = crit_mde * se
                unit = '$'
                mde_disp = mde_val
                obs_disp = obs_diff
                ctrl_disp = ctrl_mean
                pct_of_ctrl = (mde_val / ctrl_mean) * 100.0
                comp_to_obs = f"Observed=${obs_disp:+.2f} vs MDE=${mde_disp:.2f}"
                
            mde_rows.append({
                'Comparison': cfg['comparison'],
                'Scope': cfg['scope'],
                'Outcome': out,
                'N1': n1,
                'N2': n2,
                'Control_Mean': ctrl_disp,
                'MDE': mde_disp,
                'Unit': unit,
                'MDE_Pct_of_Control': pct_of_ctrl,
                'Observed_Diff': obs_disp,
                'Comparison_to_Observed': comp_to_obs
            })
            
    mde_df = pd.DataFrame(mde_rows)
    print(mde_df.to_string(index=False))
    
    return fixed_rule_results, mde_df

if __name__ == '__main__':
    run_all()
