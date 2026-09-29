import pandas as pd
import numpy as np
from sklearn.model_selection import KFold

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

margin = 0.40
cost = 0.05
groups = ['Mens-only', 'Womens-only', 'Both']

print("=== 1. GROUP-LEVEL INPUTS FOR IN-SAMPLE RULE ===")
group_rows = []
for g in groups:
    sub = df[df['purchase_history'] == g]
    n_g = len(sub)
    share = n_g / len(df)
    
    m_ctrl = sub[sub['segment'] == 'No E-Mail']['spend'].mean()
    m_mens = sub[sub['segment'] == 'Mens E-Mail']['spend'].mean()
    m_womens = sub[sub['segment'] == 'Womens E-Mail']['spend'].mean()
    
    ate_m = m_mens - m_ctrl
    ate_w = m_womens - m_ctrl
    diff_mw = ate_m - ate_w
    
    prof_m = (ate_m * margin - cost) * 1000
    prof_w = (ate_w * margin - cost) * 1000
    prof_diff = prof_m - prof_w
    
    group_rows.append({
        'Group': g,
        'N': n_g,
        'Share (%)': share * 100,
        'Control Mean': m_ctrl,
        'Mens Mean': m_mens,
        'Womens Mean': m_womens,
        'Mens ATE ($)': ate_m,
        'Womens ATE ($)': ate_w,
        'ATE Diff (M - W) ($)': diff_mw,
        'Mens Profit / 1k ($)': prof_m,
        'Womens Profit / 1k ($)': prof_w,
        'Profit Diff (M - W) / 1k ($)': prof_diff
    })

gdf = pd.DataFrame(group_rows)
print(gdf.to_string(index=False))

# Reconcile in-sample +$5.15
# For Mens-only, rule picks Mens: diff vs Mens All is 0
# For Both, rule picks Mens: diff vs Mens All is 0
# For Womens-only, rule picks Womens: diff vs Mens All is (prof_w - prof_m) * share
wo_row = [r for r in group_rows if r['Group'] == 'Womens-only'][0]
wo_gain = (wo_row['Womens Profit / 1k ($)'] - wo_row['Mens Profit / 1k ($)']) * (wo_row['Share (%)'] / 100.0)
print(f"\nWomens-only contribution to (d) over (c): {wo_gain:+.4f}")
print(f"Total in-sample (d) - (c) = {wo_gain:+.2f} per 1,000 customers")

# Check fold by fold
print("\n=== 2. DIAGNOSTIC OF CROSS-FITTING FOLDS ===")
kf = KFold(n_splits=5, shuffle=True, random_state=42)

for fold_idx, (train_idx, test_idx) in enumerate(kf.split(df)):
    tr = df.iloc[train_idx]
    te = df.iloc[test_idx]
    n_te = len(te)
    
    # Train rules
    rule = {}
    for g in groups:
        sub_tr = tr[tr['purchase_history'] == g]
        m_c = sub_tr[sub_tr['segment'] == 'No E-Mail']['spend'].mean()
        m_m = sub_tr[sub_tr['segment'] == 'Mens E-Mail']['spend'].mean()
        m_w = sub_tr[sub_tr['segment'] == 'Womens E-Mail']['spend'].mean()
        p_m = (m_m - m_c) * margin - cost
        p_w = (m_w - m_c) * margin - cost
        rule[g] = 'Mens E-Mail' if p_m >= p_w and p_m >= 0 else ('Womens E-Mail' if p_w >= 0 else 'No E-Mail')
        
    # Evaluate test fold
    # Check each group
    diffs_by_group = {}
    for g in groups:
        sub_te = te[te['purchase_history'] == g]
        w_g = len(sub_te) / n_te
        m_c = sub_te[sub_te['segment'] == 'No E-Mail']['spend'].mean()
        m_m = sub_te[sub_te['segment'] == 'Mens E-Mail']['spend'].mean()
        m_w = sub_te[sub_te['segment'] == 'Womens E-Mail']['spend'].mean()
        
        prof_m = (m_m - m_c) * margin - cost
        arm = rule[g]
        if arm == 'Mens E-Mail':
            prof_d = prof_m
        elif arm == 'Womens E-Mail':
            prof_d = (m_w - m_c) * margin - cost
        else:
            prof_d = 0.0
            
        diffs_by_group[g] = (prof_d - prof_m) * 1000 * w_g
        
    print(f"Fold {fold_idx+1}: Rule = {rule}")
    print(f"  Group-weighted diffs: {diffs_by_group}")
    print(f"  Total Fold (d - c): {sum(diffs_by_group.values()):+.4f}")
