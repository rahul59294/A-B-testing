import numpy as np
import pandas as pd
from scipy import stats
import json

def update_dashboard():
    with open('dashboard_results.json', 'r') as f:
        data = json.load(f)
        
    df = pd.read_csv('hillstrom_cleaned.csv')
    
    # 1. Add Randomization Balance
    data['randomization_balance'] = {
        'omnibus_lrt_chi2': 27.2029,
        'degrees_of_freedom': 30,
        'p_value': 0.6126,
        'max_abs_smd': 0.0142,
        'smd_threshold': 0.10,
        'conclusion': 'Randomization succeeded. Pre-treatment covariates show negligible differences across arms (all |SMD| < 0.015), and the omnibus multinomial LRT confirms balance (p = 0.613).'
    }
    
    # 2. Add Primary Arm Summaries
    data['arm_summaries'] = [
        {
            'arm': 'No E-Mail (Control)',
            'short_name': 'Control',
            'sample_size': 21306,
            'visit_rate': 10.6167,
            'visit_ci_95': [10.2038, 11.0296],
            'conversion_rate': 0.5726,
            'conversion_ci_95': [0.4714, 0.6738],
            'converters': 122,
            'mean_spend': 0.6528,
            'spend_ci_95': [0.5041, 0.8130]
        },
        {
            'arm': 'Womens E-Mail',
            'short_name': 'Womens E-Mail',
            'sample_size': 21387,
            'visit_rate': 15.1400,
            'visit_ci_95': [14.6599, 15.6202],
            'conversion_rate': 0.8837,
            'conversion_ci_95': [0.7589, 1.0085],
            'converters': 189,
            'mean_spend': 1.0772,
            'spend_ci_95': [0.8828, 1.2875]
        },
        {
            'arm': 'Mens E-Mail',
            'short_name': 'Mens E-Mail',
            'sample_size': 21307,
            'visit_rate': 18.2757,
            'visit_ci_95': [17.7579, 18.7935],
            'conversion_rate': 1.2531,
            'conversion_ci_95': [1.1037, 1.4025],
            'converters': 267,
            'mean_spend': 1.4226,
            'spend_ci_95': [1.1879, 1.6653]
        }
    ]
    
    # 3. Add Subgroup Estimates (for all 6 modifiers)
    sub_df = pd.read_csv('subgroup_estimates.csv')
    data['subgroup_estimates'] = sub_df.to_dict(orient='records')
    
    with open('dashboard_results.json', 'w') as f:
        json.dump(data, f, indent=2)
    print("Updated dashboard_results.json with balance, arm summaries, and full subgroup estimates.")

if __name__ == '__main__':
    update_dashboard()
