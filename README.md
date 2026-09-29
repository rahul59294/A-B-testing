# E-Commerce Marketing Campaign A/B Testing & Causal Uplift Analysis

[![Interactive Dashboard](https://img.shields.io/badge/Dashboard-Live%20HTML-FF6B4A?style=for-the-badge)](index.html)
[![Dataset](https://img.shields.io/badge/Dataset-Hillstrom%20MineThatData-blue?style=for-the-badge)](hillstrom_cleaned.csv)
[![Sample Size](https://img.shields.io/badge/Sample%20Size-64%2C000%20Customers-10B981?style=for-the-badge)]()
[![Methodology](https://img.shields.io/badge/Methodology-ITT%20%7C%20Holm%20FWER%20%7C%20Lin%20(2013)-8B5CF6?style=for-the-badge)]()

An end-to-end randomized controlled trial (A/B/C test) analysis evaluating the commercial performance and causal uplift of segmented email marketing campaigns on a population of **64,000 customers**.

---

## Executive Summary & Core Decision

> **Primary Strategic Recommendation: Send the Mens E-Mail to all customers.**

1. **Mens Creative Dominates Men and Dual Buyers**: The Mens creative drives massive, statistically confirmed visit rate gains on past Mens buyers (+5.8 pp visit, $p < 10^{-30}$) and dual-category buyers (+6.3 pp visit, $p < 10^{-5}$).
2. **Zero Downside on Womens-Only Buyers**: On customers who previously only bought womens merchandise, the Mens E-Mail and Womens E-Mail perform **identically** (mean spend gap is 1.6 cents, $p = 0.94$). Sending the Mens creative does **not** sacrifice revenue among women.
3. **Targeting Adds Complexity for No Real Gain**: A micro-targeting policy (routing Womens creative to women and Mens creative to others) yields an in-sample lift of only **+$2.86 per 1,000 customers** (95% bootstrap CI: [-$71.18, +$76.05]). This lift is within pure sampling error and is statistically indistinguishable from zero at any gross margin.

---

## Key Experimental Results

| Metric | Control (No Email) | Womens E-Mail | Mens E-Mail | Mens vs. Control Lift | Evidence Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Sample Size ($N$)** | 21,306 | 21,387 | 21,307 | — | Randomized 1:1:1 |
| **Visit Rate** | 10.62% | 15.14% | **18.28%** | **+7.66 pp** (+72.1% rel.) | **Confirmed** ($p < 10^{-4}$) |
| **Conversion Rate** | 0.57% | 0.88% | **1.25%** | **+0.68 pp** (+118.8% rel.) | **Confirmed** ($p < 10^{-4}$) |
| **Mean Spend ($/cust)** | $0.6528 | $1.0772 | **$1.4226** | **+$0.7698** (+117.9% rel.) | **Confirmed** ($p < 10^{-4}$) |
| **Revenue / 1k Emailed** | $652.79 | $1,077.21 | **$1,422.56** | **+$769.77** incremental | **Confirmed** |

*Note: Confirmed results survived family-wise Holm-Bonferroni correction ($\alpha = 0.05$).*

---

## Interactive Dashboard

The repository includes a self-contained, client-side interactive dashboard built with Chart.js and a light card bento-grid design system:
* **File**: [`index.html`](index.html)
* **Features**:
  - Live Unit Economics Simulator: Real-time slider recalculations for gross margins (10%–100%) and dispatch costs ($0.01–$0.40).
  - Break-Even Analysis: Dynamic break-even cost-per-email curves with conservative 95% bootstrap lower bounds.
  - Heterogeneity Explorer: Filterable views by 6 customer attributes (Purchase History, Newbie status, Channel, Zip code, History spend brackets, Recency).
  - Minimum Detectable Effect (MDE) Callout: Statistical power visualization showing why subtle creative differences on rare spend outcomes ($0.9\%$ base rate) require $0.37+ MDE to resolve.
  - Full Methodological Transparency: Always-visible limitations panel and interactive methodology drawer.

---

## Methodology & Statistical Guardrails

* **Intention-to-Treat (ITT)**: Retained all 64,000 customers as randomized; no post-treatment conditioning or survivor bias.
* **Randomization Verification**: Omnibus Multinomial Logistic Regression LRT ($\chi^2(30) = 27.20, p = 0.6126$) and Standardized Mean Differences (all $|\text{SMD}| < 0.0142$, far below the $0.10$ threshold).
* **Multiple Testing Correction**: Pre-specified test families adjusted using the step-down Holm-Bonferroni procedure to control Family-Wise Error Rate ($\alpha = 0.05$).
* **Covariate Adjustment**: Lin (2013) OLS regression adjustment with HC3 robust standard errors.
* **Nonparametric Uncertainty**: 10,000-iteration percentile bootstrap and permutation tests for heavy-tailed spend outcomes.
* **Cross-Fitting Diagnosis**: Identified and corrected finite-sample complementary partition bias ("Winner's Curse" under sample splitting) using customer-level stratified bootstrap cross-fitting (200 resamples).

---

## Repository Structure

```
├── index.html                  # Self-contained interactive Chart.js dashboard
├── dashboard_results.json      # Structured experimental results & metadata
├── hillstrom_cleaned.csv       # Cleaned ITT dataset (64,000 customers)
├── hillstrom_email_analytics.csv # Original untouched raw dataset
├── cleaning_log.md             # Data hygiene and transformation log
│
├── treatment_effects.py        # Primary treatment vs control & head-to-head tests
├── balance_and_plot.py         # Covariate balance, SMD calculations & Love plot
├── run_heterogeneity.py        # Interaction models across 6 modifiers
├── decision_analysis.py        # Unit economics & break-even models
├── resample_bootstrap.py       # Customer-level stratified bootstrap cross-fitting
├── compute_mde_fixed.py        # Minimum detectable effect & fixed-rule calculations
├── generate_dashboard.py       # Builder script for index.html
│
├── love_plot.png               # Covariate balance Love plot
├── forest_plot_visit.png       # Subgroup forest plot (visit rate)
├── forest_plot_spend.png       # Subgroup forest plot (spend)
└── profit_breakeven_chart.png  # Profit vs email dispatch cost curve
```

---

## Reproduction

All analyses run on Python 3.10+ using standard scientific computing packages:

```bash
# Clone the repository
git clone https://github.com/rahul59294/A-B-testing.git
cd A-B-testing

# Install dependencies
pip install numpy pandas scipy statsmodels matplotlib scikit-learn

# Run primary treatment effects
python treatment_effects.py

# Run heterogeneity interaction tests
python run_heterogeneity.py

# Rebuild dashboard results
python build_dashboard_results.py

# Launch interactive dashboard
open index.html
```

---

## Citation & Attribution

* **Data Source**: Kevin Hillstrom, *MineThatData E-Mail Analytics Challenge* (2008), available via [`scikit-uplift`](https://scikit-uplift.readthedocs.io/).
* **Author**: Rahul Kumar Singh
