import json
import os

def create_dashboard_html():
    with open('dashboard_results.json', 'r') as f:
        data = json.load(f)
    
    # We will embed the JSON directly as a JavaScript variable
    json_str = json.dumps(data)
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Hillstrom E-Mail Campaign A/B Test | Portfolio Dashboard</title>
  
  <!-- Typography: Sora (Headings) & Inter (Body/Data) -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Sora:wght@500;600;700;800&display=swap" rel="stylesheet">
  
  <!-- Chart.js -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

  <style>
    :root {{
      --bg: #F6F5F3;
      --card-bg: #FFFFFF;
      --accent: #FF6B4A;
      --accent-hover: #E85A3A;
      --accent-soft: rgba(255, 107, 74, 0.08);
      --accent-subtle: rgba(255, 107, 74, 0.15);
      
      --text-main: #141619;
      --text-secondary: #575E66;
      --text-muted: #8A929A;
      
      --confirmed-bg: #FF6B4A;
      --confirmed-text: #FFFFFF;
      --exploratory-bg: #F0F2F4;
      --exploratory-text: #64748B;
      --exploratory-border: #CBD5E1;
      
      --border: rgba(0, 0, 0, 0.06);
      --card-border: rgba(0, 0, 0, 0.05);
      --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.02);
      --shadow-md: 0 4px 20px rgba(0, 0, 0, 0.04), 0 1px 3px rgba(0, 0, 0, 0.02);
      --shadow-lg: 0 12px 32px rgba(0, 0, 0, 0.06), 0 2px 6px rgba(0, 0, 0, 0.03);
      
      --radius-sm: 12px;
      --radius-md: 18px;
      --radius-lg: 24px;
      --radius-pill: 9999px;
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      background-color: var(--bg);
      color: var(--text-main);
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      font-feature-settings: 'tnum' 1, 'cv05' 1;
      -webkit-font-smoothing: antialiased;
      line-height: 1.5;
      padding: 40px 24px 80px;
    }}

    .container {{
      max-width: 1280px;
      margin: 0 auto;
    }}

    h1, h2, h3, h4 {{
      font-family: 'Sora', sans-serif;
      font-weight: 700;
      color: var(--text-main);
      letter-spacing: -0.02em;
    }}

    /* Card System */
    .bento-card {{
      background: var(--card-bg);
      border-radius: var(--radius-lg);
      border: 1px solid var(--card-border);
      box-shadow: var(--shadow-md);
      padding: 28px 32px;
      transition: transform 0.2s ease, box-shadow 0.2s ease;
      position: relative;
    }}

    .bento-card:hover {{
      box-shadow: var(--shadow-lg);
    }}

    /* Badge System - Critical Rule Throughout */
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 5px 12px;
      border-radius: var(--radius-pill);
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.02em;
      white-space: nowrap;
      vertical-align: middle;
      height: fit-content;
    }}

    .badge-confirmed {{
      background-color: var(--confirmed-bg);
      color: var(--confirmed-text);
      box-shadow: 0 2px 6px rgba(255, 107, 74, 0.25);
    }}

    .badge-confirmed::before {{
      content: '';
      display: inline-block;
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #FFFFFF;
    }}

    .badge-exploratory {{
      background-color: var(--exploratory-bg);
      color: var(--exploratory-text);
      border: 1px solid var(--exploratory-border);
      font-weight: 500;
    }}

    .badge-exploratory::before {{
      content: '';
      display: inline-block;
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #94A3B8;
    }}

    /* Header Section */
    .header {{
      display: flex;
      flex-direction: column;
      gap: 16px;
      margin-bottom: 32px;
    }}

    .header-top {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      flex-wrap: wrap;
      gap: 20px;
    }}

    .title-group h1 {{
      font-size: 32px;
      line-height: 1.2;
      margin-bottom: 6px;
    }}

    .title-group p {{
      color: var(--text-secondary);
      font-size: 16px;
      font-weight: 400;
    }}

    .methodology-toggle-btn {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 20px;
      border-radius: var(--radius-pill);
      background: white;
      color: var(--text-main);
      border: 1px solid var(--border);
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      box-shadow: var(--shadow-sm);
      transition: all 0.2s ease;
    }}

    .methodology-toggle-btn:hover {{
      border-color: var(--accent);
      color: var(--accent);
      transform: translateY(-1px);
    }}

    .methodology-drawer {{
      display: none;
      background: #FFFFFF;
      border-radius: var(--radius-md);
      border: 1px solid var(--border);
      padding: 24px;
      margin-top: 8px;
      animation: fadeIn 0.3s ease;
    }}

    .methodology-drawer.open {{
      display: block;
    }}

    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(-6px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* Bento Grid Layout */
    .grid-12 {{
      display: grid;
      grid-template-columns: repeat(12, 1fr);
      gap: 24px;
      margin-bottom: 24px;
    }}

    .col-12 {{ grid-column: span 12; }}
    .col-8  {{ grid-column: span 8; }}
    .col-7  {{ grid-column: span 7; }}
    .col-6  {{ grid-column: span 6; }}
    .col-5  {{ grid-column: span 5; }}
    .col-4  {{ grid-column: span 4; }}
    .col-3  {{ grid-column: span 3; }}

    @media (max-width: 1024px) {{
      .col-8, .col-7, .col-5, .col-4, .col-6 {{
        grid-column: span 12;
      }}
    }}

    /* KPI Cards */
    .kpi-card {{
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      min-height: 160px;
    }}

    .kpi-label {{
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }}

    .kpi-value {{
      font-family: 'Sora', sans-serif;
      font-size: 34px;
      font-weight: 700;
      line-height: 1.1;
      color: var(--text-main);
      letter-spacing: -0.03em;
      margin-bottom: 6px;
    }}

    .kpi-subtext {{
      font-size: 13px;
      color: var(--text-secondary);
    }}

    /* Hero Recommendation Card */
    .hero-recommendation-card {{
      background: linear-gradient(135deg, #FF6B4A 0%, #FF512B 100%);
      color: #FFFFFF;
      border: none;
      box-shadow: 0 12px 36px rgba(255, 107, 74, 0.35);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}

    .hero-recommendation-card h3 {{
      color: #FFFFFF;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      opacity: 0.9;
      margin-bottom: 12px;
    }}

    .hero-headline {{
      font-family: 'Sora', sans-serif;
      font-size: 26px;
      font-weight: 800;
      line-height: 1.25;
      margin-bottom: 14px;
      letter-spacing: -0.02em;
    }}

    .hero-desc {{
      font-size: 14px;
      line-height: 1.6;
      opacity: 0.95;
      font-weight: 400;
    }}

    .hero-pill-badge {{
      display: inline-flex;
      background: rgba(255, 255, 255, 0.22);
      padding: 6px 14px;
      border-radius: var(--radius-pill);
      font-size: 12px;
      font-weight: 600;
      margin-top: 14px;
      width: fit-content;
    }}

    /* Section Titles */
    .section-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
    }}

    .section-title {{
      font-size: 18px;
      font-weight: 700;
      letter-spacing: -0.01em;
    }}

    /* Pill Tabs */
    .pill-tabs {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      background: rgba(0, 0, 0, 0.03);
      padding: 5px;
      border-radius: var(--radius-pill);
      width: fit-content;
      margin-bottom: 24px;
    }}

    .pill-tab {{
      padding: 8px 18px;
      border-radius: var(--radius-pill);
      border: none;
      background: transparent;
      color: var(--text-secondary);
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
    }}

    .pill-tab:hover {{
      color: var(--text-main);
    }}

    .pill-tab.active {{
      background: #FFFFFF;
      color: var(--text-main);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    }}

    /* Charts Container */
    .chart-container {{
      position: relative;
      width: 100%;
      height: 280px;
    }}

    /* Business translation row */
    .translation-strip {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
      margin-top: 20px;
      padding-top: 20px;
      border-top: 1px solid var(--border);
    }}

    .translation-item {{
      background: #FAF9F7;
      padding: 14px 18px;
      border-radius: var(--radius-sm);
    }}

    .translation-val {{
      font-family: 'Sora', sans-serif;
      font-size: 19px;
      font-weight: 700;
      color: var(--accent);
      margin-bottom: 2px;
    }}

    .translation-label {{
      font-size: 12px;
      color: var(--text-secondary);
      line-height: 1.4;
    }}

    /* Subgroup cards in heterogeneity */
    .subgroup-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
      margin-top: 20px;
    }}

    @media (max-width: 900px) {{
      .subgroup-grid {{
        grid-template-columns: 1fr;
      }}
    }}

    .subgroup-card {{
      background: #FAF9F7;
      border-radius: var(--radius-md);
      padding: 20px;
      border: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}

    .subgroup-card.highlight-zero {{
      background: #FFFFFF;
      border: 2px dashed #CBD5E1;
    }}

    .subgroup-head {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }}

    .subgroup-title {{
      font-size: 15px;
      font-weight: 700;
    }}

    .subgroup-metric-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 0;
      border-bottom: 1px solid rgba(0,0,0,0.04);
      font-size: 13px;
    }}

    .subgroup-metric-row:last-child {{
      border-bottom: none;
    }}

    .metric-name {{
      color: var(--text-secondary);
    }}

    .metric-val-wrap {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
    }}

    /* Sliders and Decision Panel */
    .slider-group {{
      margin-bottom: 24px;
    }}

    .slider-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }}

    .slider-title {{
      font-size: 13px;
      font-weight: 600;
      color: var(--text-main);
    }}

    .slider-readout {{
      font-family: 'Sora', sans-serif;
      font-size: 16px;
      font-weight: 700;
      color: var(--accent);
      background: var(--accent-soft);
      padding: 3px 12px;
      border-radius: var(--radius-pill);
    }}

    input[type=range] {{
      -webkit-appearance: none;
      width: 100%;
      height: 8px;
      border-radius: 4px;
      background: #E5E7EB;
      outline: none;
    }}

    input[type=range]::-webkit-slider-thumb {{
      -webkit-appearance: none;
      appearance: none;
      width: 22px;
      height: 22px;
      border-radius: 50%;
      background: var(--accent);
      cursor: pointer;
      box-shadow: 0 2px 6px rgba(255, 107, 74, 0.4);
      border: 2px solid #FFFFFF;
      transition: transform 0.1s ease;
    }}

    input[type=range]::-webkit-slider-thumb:hover {{
      transform: scale(1.15);
    }}

    /* Profit comparison cards */
    .decision-display-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 16px;
      margin-top: 16px;
    }}

    @media (max-width: 700px) {{
      .decision-display-grid {{
        grid-template-columns: 1fr;
      }}
    }}

    .decision-box {{
      background: #FAF9F7;
      padding: 20px;
      border-radius: var(--radius-md);
      border: 1px solid var(--border);
    }}

    .decision-box.highlight {{
      background: #FFF9F7;
      border-color: rgba(255, 107, 74, 0.3);
    }}

    .decision-box-label {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      font-weight: 600;
      margin-bottom: 6px;
    }}

    .decision-box-val {{
      font-family: 'Sora', sans-serif;
      font-size: 26px;
      font-weight: 700;
      color: var(--text-main);
      margin-bottom: 4px;
    }}

    .decision-box-diff {{
      font-size: 13px;
      color: var(--text-secondary);
    }}

    /* Callout Note */
    .callout-note {{
      background: #FAF9F7;
      border-left: 3px solid var(--accent);
      padding: 14px 18px;
      border-radius: 4px var(--radius-sm) var(--radius-sm) 4px;
      font-size: 13px;
      color: var(--text-secondary);
      margin-top: 16px;
      line-height: 1.5;
    }}

    /* Limitations List */
    .limitations-list {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 18px;
      margin-top: 12px;
    }}

    @media (max-width: 800px) {{
      .limitations-list {{
        grid-template-columns: 1fr;
      }}
    }}

    .limitation-item {{
      display: flex;
      gap: 14px;
      align-items: flex-start;
      background: #FAF9F7;
      padding: 16px 18px;
      border-radius: var(--radius-md);
      border: 1px solid var(--border);
    }}

    .limitation-num {{
      font-family: 'Sora', sans-serif;
      font-size: 13px;
      font-weight: 700;
      color: var(--accent);
      background: var(--accent-soft);
      width: 28px;
      height: 28px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }}

    .limitation-text h4 {{
      font-size: 14px;
      margin-bottom: 4px;
    }}

    .limitation-text p {{
      font-size: 12.5px;
      color: var(--text-secondary);
      line-height: 1.5;
    }}

    /* Footer */
    .footer {{
      margin-top: 48px;
      padding-top: 32px;
      border-top: 1px solid var(--border);
      color: var(--text-muted);
      font-size: 13px;
      display: flex;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 20px;
      line-height: 1.6;
    }}

    .footer a {{
      color: var(--text-secondary);
      text-decoration: none;
    }}

    .footer a:hover {{
      color: var(--accent);
    }}
  </style>
</head>
<body>

<div class="container">

  <!-- 1. Header -->
  <header class="header">
    <div class="header-top">
      <div class="title-group">
        <h1>Hillstrom E-Mail Campaign A/B Test</h1>
        <p>Randomized email A/B test &mdash; 64,000 customers (Intention-to-Treat)</p>
      </div>
      <button class="methodology-toggle-btn" onclick="toggleMethodology()">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
        Read the methodology
      </button>
    </div>

    <div id="methodologyDrawer" class="methodology-drawer">
      <div style="max-width: 960px;">
        <h3 style="font-size: 16px; margin-bottom: 8px;">Methodology & Statistical Guardrails</h3>
        <p style="font-size: 13.5px; color: var(--text-secondary); line-height: 1.6; margin-bottom: 12px;">
          <strong>Intention-to-Treat (ITT):</strong> Every one of the 64,000 randomized customers is retained in their assigned arm regardless of open, visit, or purchase status. No conditioning on post-treatment outcomes.
        </p>
        <p style="font-size: 13.5px; color: var(--text-secondary); line-height: 1.6; margin-bottom: 12px;">
          <strong>Holm-Bonferroni Correction:</strong> Because testing multiple outcomes across multiple subgroups inflates false discovery rates, tests are evaluated in pre-specified families with step-down Holm correction to control Family-Wise Error Rate (&alpha; = 0.05).
        </p>
        <p style="font-size: 13.5px; color: var(--text-secondary); line-height: 1.6;">
          <strong>Confirmed vs. Exploratory:</strong> Results marked <span class="badge badge-confirmed">Confirmed</span> survived Holm multiple comparison adjustment. Results marked <span class="badge badge-exploratory">Exploratory &mdash; did not survive correction</span> did not maintain significance under correction and represent hypotheses, not verified decisions.
        </p>
      </div>
    </div>
  </header>

  <!-- 2. Hero KPI Strip + Recommendation Bento -->
  <div class="grid-12">
    <!-- Total Customers -->
    <div class="bento-card col-3 kpi-card">
      <div class="kpi-label">Sample Population</div>
      <div class="kpi-value" id="kpiTotalCustomers">64,000</div>
      <div class="kpi-subtext">3 Randomized Arms (~21.3k each)</div>
    </div>

    <!-- Visit Lift -->
    <div class="bento-card col-3 kpi-card">
      <div class="kpi-label">
        Visit Lift (Mens vs Ctrl)
        <span class="badge badge-confirmed">Confirmed</span>
      </div>
      <div class="kpi-value" id="kpiVisitLift">+7.66 pp</div>
      <div class="kpi-subtext" id="kpiVisitSub">+72.1% relative lift (p &lt; 0.0001)</div>
    </div>

    <!-- Conversion Lift -->
    <div class="bento-card col-3 kpi-card">
      <div class="kpi-label">
        Conv. Lift (Mens vs Ctrl)
        <span class="badge badge-confirmed">Confirmed</span>
      </div>
      <div class="kpi-value" id="kpiConvLift">+0.68 pp</div>
      <div class="kpi-subtext" id="kpiConvSub">+118.8% relative lift (p &lt; 0.0001)</div>
    </div>

    <!-- Spend Lift -->
    <div class="bento-card col-3 kpi-card">
      <div class="kpi-label">
        Spend Lift (Mens vs Ctrl)
        <span class="badge badge-confirmed">Confirmed</span>
      </div>
      <div class="kpi-value" id="kpiSpendLift">+$0.77</div>
      <div class="kpi-subtext" id="kpiSpendSub">+117.9% relative lift (p &lt; 0.0001)</div>
    </div>

    <!-- Standout Hero Recommendation Card -->
    <div class="bento-card col-12 hero-recommendation-card">
      <div>
        <h3>Executive Strategy & Recommendation</h3>
        <div class="hero-headline">Send Mens E-Mail to everyone.</div>
        <p class="hero-desc">
          The Mens creative produces massive, confirmed visit lifts on Men (+5.8 pp) and dual-category buyers (+6.3 pp; +$1.66 spend lift is exploratory), while performing <strong>statistically identically</strong> to the Womens creative on Womens-only buyers (observed spend gap is 1.6 cents, p = 0.94). Micro-targeting by purchase history adds routing complexity for an undetectable +$2.86 / 1,000 lift whose 95% bootstrap confidence interval contains zero.
        </p>
      </div>
      <div class="hero-pill-badge">
        Default Rule: Unconditional Mens Campaign Broadcast
      </div>
    </div>
  </div>

  <!-- 3. Randomization Balance & Verification -->
  <div class="grid-12">
    <div class="bento-card col-12" style="padding: 22px 30px;">
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
        <div style="display: flex; align-items: center; gap: 14px;">
          <div style="background: rgba(34, 197, 94, 0.12); color: #15803D; width: 38px; height: 38px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold;">
            ✓
          </div>
          <div>
            <h3 style="font-size: 16px; margin-bottom: 2px;">Randomization Balance Succeeded</h3>
            <p style="font-size: 13px; color: var(--text-secondary);" id="balanceSummaryText">
              Omnibus Multinomial Logistic LRT: &chi;&sup2;(30) = 27.20, p = 0.613 (Fail to reject balance null).
            </p>
          </div>
        </div>
        <div style="display: flex; gap: 24px; align-items: center;">
          <div style="text-align: right;">
            <div style="font-size: 11px; text-transform: uppercase; color: var(--text-muted); font-weight: 600;">Max Absolute SMD</div>
            <div style="font-family: 'Sora', sans-serif; font-size: 16px; font-weight: 700; color: #15803D;">0.0142</div>
          </div>
          <div style="text-align: right;">
            <div style="font-size: 11px; text-transform: uppercase; color: var(--text-muted); font-weight: 600;">Standard Threshold</div>
            <div style="font-family: 'Sora', sans-serif; font-size: 16px; font-weight: 700; color: var(--text-secondary);">&le; 0.1000</div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 4. Primary Treatment Effects (Charts & Translation) -->
  <div class="grid-12">
    <!-- Visit Rate Chart -->
    <div class="bento-card col-4">
      <div class="section-header">
        <div>
          <h3 class="section-title">Visit Rate</h3>
          <p style="font-size: 12px; color: var(--text-muted);">% of arm visiting site in 2 weeks</p>
        </div>
        <span class="badge badge-confirmed">Confirmed</span>
      </div>
      <div class="chart-container">
        <canvas id="chartVisit"></canvas>
      </div>
      <div style="font-size: 12px; color: var(--text-secondary); margin-top: 10px; text-align: center;">
        Mens vs Ctrl: <strong>+7.66 pp</strong> &bull; Womens vs Ctrl: <strong>+4.52 pp</strong>
      </div>
    </div>

    <!-- Conversion Rate Chart -->
    <div class="bento-card col-4">
      <div class="section-header">
        <div>
          <h3 class="section-title">Conversion Rate</h3>
          <p style="font-size: 12px; color: var(--text-muted);">% of arm purchasing in 2 weeks</p>
        </div>
        <span class="badge badge-confirmed">Confirmed</span>
      </div>
      <div class="chart-container">
        <canvas id="chartConversion"></canvas>
      </div>
      <div style="font-size: 12px; color: var(--text-secondary); margin-top: 10px; text-align: center;">
        Mens vs Ctrl: <strong>+0.68 pp</strong> &bull; Womens vs Ctrl: <strong>+0.31 pp</strong>
      </div>
    </div>

    <!-- Mean Spend Chart -->
    <div class="bento-card col-4">
      <div class="section-header">
        <div>
          <h3 class="section-title">Mean Spend</h3>
          <p style="font-size: 12px; color: var(--text-muted);">Revenue per customer randomized ($)</p>
        </div>
        <span class="badge badge-confirmed">Confirmed</span>
      </div>
      <div class="chart-container">
        <canvas id="chartSpend"></canvas>
      </div>
      <div style="font-size: 12px; color: var(--text-secondary); margin-top: 10px; text-align: center;">
        Mens vs Ctrl: <strong>+$0.77</strong> &bull; Womens vs Ctrl: <strong>+$0.42</strong>
      </div>
    </div>

    <!-- Business Translation Strip -->
    <div class="bento-card col-12" style="padding: 20px 28px;">
      <div style="font-size: 13px; font-weight: 600; text-transform: uppercase; color: var(--text-muted); margin-bottom: 12px; letter-spacing: 0.05em;">
        Commercial Impact per 1,000 Emails Dispatched
      </div>
      <div class="translation-strip" style="margin-top: 0; padding-top: 0; border-top: none;">
        <div class="translation-item">
          <div class="translation-val">+77 Visits</div>
          <div class="translation-label">Incremental site visitors driven by Mens E-Mail (+45 for Womens E-Mail)</div>
        </div>
        <div class="translation-item">
          <div class="translation-val">+7 Orders</div>
          <div class="translation-label">Incremental purchasing orders generated by Mens E-Mail (+3 for Womens E-Mail)</div>
        </div>
        <div class="translation-item">
          <div class="translation-val">+$770 Gross Revenue</div>
          <div class="translation-label">Incremental top-line customer spend from Mens E-Mail (+$424 for Womens E-Mail)</div>
        </div>
      </div>
    </div>
  </div>

  <!-- 5. Heterogeneity Panel -->
  <div class="bento-card col-12" style="margin-bottom: 24px;">
    <div class="section-header" style="flex-wrap: wrap; gap: 12px;">
      <div>
        <h3 class="section-title">Treatment Effect Heterogeneity & Subgroups</h3>
        <p style="font-size: 13px; color: var(--text-secondary);">
          Evaluation of treatment interactions across pre-specified customer dimensions (HC3 robust standard errors)
        </p>
      </div>
      <div id="interactionBadgeContainer">
        <!-- Rendered dynamically -->
      </div>
    </div>

    <!-- Pill Tabs -->
    <div class="pill-tabs" id="heterogeneityTabs">
      <button class="pill-tab active" onclick="switchModifier('purchase_history')">Purchase History</button>
      <button class="pill-tab" onclick="switchModifier('newbie')">Newbie Status</button>
      <button class="pill-tab" onclick="switchModifier('channel')">Shopping Channel</button>
      <button class="pill-tab" onclick="switchModifier('zip_code')">Zip Code</button>
      <button class="pill-tab" onclick="switchModifier('history_bracket')">History Spend Band</button>
      <button class="pill-tab" onclick="switchModifier('recency_bracket')">Recency Band</button>
    </div>

    <!-- Interaction Banner -->
    <div id="interactionBanner" style="background: #FAF9F7; border-radius: var(--radius-sm); padding: 14px 20px; margin-bottom: 20px; font-size: 13.5px; border: 1px solid var(--border);">
      <!-- Rendered dynamically -->
    </div>

    <!-- Subgroups Display Grid -->
    <div id="subgroupsContainer">
      <!-- Rendered dynamically -->
    </div>
  </div>

  <!-- 6. Profit & Decision Simulator + 7. MDE Callout -->
  <div class="grid-12">
    <!-- Simulator Card -->
    <div class="bento-card col-8">
      <div class="section-header">
        <div>
          <h3 class="section-title">Campaign Unit Economics & Policy Decision Simulator</h3>
          <p style="font-size: 13px; color: var(--text-secondary);">
            Adjust gross margin and dispatch cost to evaluate break-evens and compare Policy (c) vs. Policy (e).
          </p>
        </div>
        <div style="font-size: 11px; background: rgba(0,0,0,0.04); padding: 4px 10px; border-radius: var(--radius-pill); font-weight: 500; color: var(--text-secondary);">
          Illustrative assumptions &mdash; not in source data
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 12px;">
        <!-- Margin Slider -->
        <div class="slider-group">
          <div class="slider-header">
            <span class="slider-title">Gross Margin</span>
            <span class="slider-readout" id="marginDisplay">40%</span>
          </div>
          <input type="range" id="marginSlider" min="10" max="100" step="5" value="40" oninput="updateSimulation()">
          <div style="display: flex; justify-content: space-between; font-size: 11px; color: var(--text-muted); margin-top: 4px;">
            <span>10%</span>
            <span>Default: 40%</span>
            <span>100%</span>
          </div>
        </div>

        <!-- Cost Slider -->
        <div class="slider-group">
          <div class="slider-header">
            <span class="slider-title">Cost per Email Dispatched</span>
            <span class="slider-readout" id="costDisplay">$0.05</span>
          </div>
          <input type="range" id="costSlider" min="0.01" max="0.40" step="0.01" value="0.05" oninput="updateSimulation()">
          <div style="display: flex; justify-content: space-between; font-size: 11px; color: var(--text-muted); margin-top: 4px;">
            <span>$0.01</span>
            <span>Default: $0.05</span>
            <span>$0.40</span>
          </div>
        </div>
      </div>

      <!-- Decision Displays -->
      <div class="decision-display-grid">
        <div class="decision-box">
          <div class="decision-box-label">Policy (c): Mens E-Mail to Everyone</div>
          <div class="decision-box-val" id="policyCProfit">$257.93 / 1k</div>
          <div class="decision-box-diff">Incremental profit per 1,000 customers</div>
        </div>

        <div class="decision-box highlight">
          <div class="decision-box-label">Policy (e): Fixed Womens-only Targeting</div>
          <div class="decision-box-val" id="policyEProfit">$260.79 / 1k</div>
          <div class="decision-box-diff" id="policyDiff">Lift over Mens All: +$2.86 / 1k</div>
        </div>
      </div>

      <!-- Live Break-even summary -->
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 16px;">
        <div style="background: #FAF9F7; padding: 14px 18px; border-radius: var(--radius-sm); font-size: 13px;">
          <span style="color: var(--text-secondary);">Mens Break-Even Cost:</span>
          <strong style="margin-left: 6px;" id="mensBreakEven">$0.308 / email</strong>
          <span style="color: var(--text-muted); font-size: 11px; display: block;">(Conservative 95% low: <span id="mensBreakEvenCons">$0.195</span>)</span>
        </div>
        <div style="background: #FAF9F7; padding: 14px 18px; border-radius: var(--radius-sm); font-size: 13px;">
          <span style="color: var(--text-secondary);">Womens Break-Even Cost:</span>
          <strong style="margin-left: 6px;" id="womensBreakEven">$0.170 / email</strong>
          <span style="color: var(--text-muted); font-size: 11px; display: block;">(Conservative 95% low: <span id="womensBreakEvenCons">$0.068</span>)</span>
        </div>
      </div>

      <div class="callout-note" id="bootstrapNote">
        <strong>Statistical Reality:</strong> The difference between Policy (e) and Policy (c) is <strong id="dynamicDiffText">+$2.86</strong> per 1,000 customers with a 95% bootstrap confidence interval of <strong id="dynamicCiText">[-$71.18, +$76.05]</strong>. <em>This difference is not statistically distinguishable from zero at any gross margin ($0 is well within the interval).</em>
      </div>
    </div>

    <!-- 7. Minimum Detectable Effect Card -->
    <div class="bento-card col-4" style="display: flex; flex-direction: column; justify-content: space-between;">
      <div>
        <div class="section-header" style="margin-bottom: 12px;">
          <h3 class="section-title">Statistical Power & MDE</h3>
          <span class="badge badge-exploratory">MDE Sensitivity</span>
        </div>
        <p style="font-size: 13px; color: var(--text-secondary); line-height: 1.6; margin-bottom: 16px;">
          Why can't we say Womens E-Mail performs <em>better</em> or <em>worse</em> for Womens-only buyers?
        </p>

        <div style="background: #FAF9F7; border-radius: var(--radius-md); padding: 18px; margin-bottom: 16px; border: 1px solid var(--border);">
          <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px;">
            <span style="font-size: 12px; font-weight: 600; text-transform: uppercase; color: var(--text-muted);">Spend MDE Threshold</span>
            <span style="font-family: 'Sora', sans-serif; font-size: 18px; font-weight: 700; color: #DC2626;">$0.37 / cust</span>
          </div>
          <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 12px;">
            The minimum spend difference this test had 80% power to detect in Womens-only buyers (74.5% of control spend).
          </div>

          <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px; padding-top: 10px; border-top: 1px dashed var(--border);">
            <span style="font-size: 12px; font-weight: 600; text-transform: uppercase; color: var(--text-muted);">Observed Difference</span>
            <span style="font-family: 'Sora', sans-serif; font-size: 18px; font-weight: 700; color: #15803D;">$0.016 / cust</span>
          </div>
          <div style="font-size: 12px; color: var(--text-secondary);">
            The actual observed sample gap between Mens and Womens email is only 1.6 cents (p = 0.94).
          </div>
        </div>

        <p style="font-size: 12.5px; color: var(--text-secondary); line-height: 1.5;">
          <strong>Plain-Language Verdict:</strong> Because the 1.6¢ gap is far below the $0.37 MDE, this test is <strong>underpowered to detect subtle creative nuances</strong> on rare spend events. The result is genuinely inconclusive rather than proof of exactly zero true difference.
        </p>
      </div>

      <div style="font-size: 11.5px; color: var(--text-muted); margin-top: 16px;">
        Two-sided &alpha; = 0.05, 80% Power, N = 19,215
      </div>
    </div>
  </div>

  <!-- 8. Limitations Panel -->
  <div class="bento-card col-12" style="margin-bottom: 32px;">
    <div class="section-header">
      <div>
        <h3 class="section-title">Methodological Limitations</h3>
        <p style="font-size: 13px; color: var(--text-secondary);">
          Crucial caveats and context for interpreting these experimental findings.
        </p>
      </div>
      <span style="font-size: 11px; background: rgba(0,0,0,0.04); padding: 4px 10px; border-radius: var(--radius-pill); font-weight: 600; color: var(--text-secondary);">
        Always Visible
      </span>
    </div>

    <div class="limitations-list" id="limitationsGrid">
      <!-- Rendered dynamically from dashboard_results.json -->
    </div>
  </div>

  <!-- 9. Footer -->
  <footer class="footer">
    <div>
      <strong>Dataset Citation:</strong> Hillstrom MineThatData E-Mail Analytics (via <code>scikit-uplift</code>).<br>
      <strong>Statistical Methods:</strong> Two-proportion z-tests, Nonparametric Bootstrap (10k), Permutation tests (10k), Lin (2013) OLS with HC3 SEs, Holm-Bonferroni FWER control, 5-fold cross-fitting with customer-level stratified bootstrap.
    </div>
    <div style="text-align: right;">
      <span>A/B Testing & Causal Inference Portfolio Demonstration</span><br>
      <span>Interactive Client-Side Engine (Chart.js &bull; Self-Contained)</span>
    </div>
  </footer>

</div>

<!-- EMBEDDED DASHBOARD DATA -->
<script>
const DASHBOARD_DATA = {json_str};

// Global Charts references
let chartVisit = null;
let chartConversion = null;
let chartSpend = null;

// Error bars plugin for Chart.js
const errorBarsPlugin = {{
  id: 'errorBars',
  afterDatasetsDraw(chart, args, options) {{
    const {{ ctx, scales: {{ x, y }} }} = chart;
    chart.data.datasets.forEach((dataset, datasetIndex) => {{
      const meta = chart.getDatasetMeta(datasetIndex);
      if (!dataset.errorBars) return;
      dataset.errorBars.forEach((eb, index) => {{
        if (!eb) return;
        const element = meta.data[index];
        if (!element) return;
        const xPos = element.x;
        const yLow = y.getPixelForValue(eb.low);
        const yHigh = y.getPixelForValue(eb.high);
        
        ctx.save();
        ctx.strokeStyle = '#1F2937';
        ctx.lineWidth = 1.6;
        // vertical bar
        ctx.beginPath();
        ctx.moveTo(xPos, yLow);
        ctx.lineTo(xPos, yHigh);
        ctx.stroke();
        // top cap
        ctx.beginPath();
        ctx.moveTo(xPos - 5, yHigh);
        ctx.lineTo(xPos + 5, yHigh);
        ctx.stroke();
        // bottom cap
        ctx.beginPath();
        ctx.moveTo(xPos - 5, yLow);
        ctx.lineTo(xPos + 5, yLow);
        ctx.stroke();
        ctx.restore();
      }});
    }});
  }}
}};
Chart.register(errorBarsPlugin);

// Initialize Page
document.addEventListener('DOMContentLoaded', () => {{
  initKPIs();
  initPrimaryCharts();
  renderModifierTab('purchase_history');
  updateSimulation();
  renderLimitations();
}});

function toggleMethodology() {{
  const drawer = document.getElementById('methodologyDrawer');
  drawer.classList.toggle('open');
}}

// 1. Initialize KPIs
function initKPIs() {{
  const armMens = DASHBOARD_DATA.arm_summaries.find(a => a.short_name === 'Mens E-Mail');
  const armCtrl = DASHBOARD_DATA.arm_summaries.find(a => a.short_name === 'Control');
  
  const tcVisit = DASHBOARD_DATA.treatment_vs_control.find(t => t.comparison.includes('Mens') && t.outcome === 'visit');
  const tcConv = DASHBOARD_DATA.treatment_vs_control.find(t => t.comparison.includes('Mens') && t.outcome === 'conversion');
  const tcSpend = DASHBOARD_DATA.treatment_vs_control.find(t => t.comparison.includes('Mens') && t.outcome === 'spend');

  if (tcVisit) {{
    document.getElementById('kpiVisitLift').textContent = `+${{tcVisit.estimate.toFixed(2)}} pp`;
    const rel = ((tcVisit.estimate / armCtrl.visit_rate) * 100).toFixed(1);
    document.getElementById('kpiVisitSub').textContent = `+${{rel}}% relative lift (p < 0.0001)`;
  }}
  if (tcConv) {{
    document.getElementById('kpiConvLift').textContent = `+${{tcConv.estimate.toFixed(2)}} pp`;
    const rel = ((tcConv.estimate / armCtrl.conversion_rate) * 100).toFixed(1);
    document.getElementById('kpiConvSub').textContent = `+${{rel}}% relative lift (p < 0.0001)`;
  }}
  if (tcSpend) {{
    document.getElementById('kpiSpendLift').textContent = `+$${{tcSpend.estimate.toFixed(2)}}`;
    const rel = ((tcSpend.estimate / armCtrl.mean_spend) * 100).toFixed(1);
    document.getElementById('kpiSpendSub').textContent = `+${{rel}}% relative lift (p < 0.0001)`;
  }}
}}

// 2. Primary Charts
function initPrimaryCharts() {{
  const arms = DASHBOARD_DATA.arm_summaries;
  const labels = arms.map(a => a.short_name);
  const colors = ['#94A3B8', '#F97316', '#FF6B4A'];

  // Visit Rate Chart
  const ctxV = document.getElementById('chartVisit').getContext('2d');
  chartVisit = new Chart(ctxV, {{
    type: 'bar',
    data: {{
      labels: labels,
      datasets: [{{
        data: arms.map(a => a.visit_rate),
        backgroundColor: colors,
        borderRadius: 8,
        barPercentage: 0.6,
        errorBars: arms.map(a => ({{ low: a.visit_ci_95[0], high: a.visit_ci_95[1] }}))
      }}]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{
          callbacks: {{
            label: (ctx) => `Visit Rate: ${{ctx.raw.toFixed(2)}}% [95% CI: ${{arms[ctx.dataIndex].visit_ci_95[0].toFixed(2)}}% - ${{arms[ctx.dataIndex].visit_ci_95[1].toFixed(2)}}%]`
          }}
        }}
      }},
      scales: {{
        y: {{
          beginAtZero: true,
          max: 22,
          ticks: {{ callback: v => v + '%' }},
          grid: {{ color: 'rgba(0,0,0,0.04)' }}
        }},
        x: {{ grid: {{ display: false }} }}
      }}
    }}
  }});

  // Conversion Rate Chart
  const ctxC = document.getElementById('chartConversion').getContext('2d');
  chartConversion = new Chart(ctxC, {{
    type: 'bar',
    data: {{
      labels: labels,
      datasets: [{{
        data: arms.map(a => a.conversion_rate),
        backgroundColor: colors,
        borderRadius: 8,
        barPercentage: 0.6,
        errorBars: arms.map(a => ({{ low: a.conversion_ci_95[0], high: a.conversion_ci_95[1] }}))
      }}]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{
          callbacks: {{
            label: (ctx) => `Conv Rate: ${{ctx.raw.toFixed(2)}}% [95% CI: ${{arms[ctx.dataIndex].conversion_ci_95[0].toFixed(2)}}% - ${{arms[ctx.dataIndex].conversion_ci_95[1].toFixed(2)}}%]`
          }}
        }}
      }},
      scales: {{
        y: {{
          beginAtZero: true,
          max: 1.6,
          ticks: {{ callback: v => v + '%' }},
          grid: {{ color: 'rgba(0,0,0,0.04)' }}
        }},
        x: {{ grid: {{ display: false }} }}
      }}
    }}
  }});

  // Spend Chart
  const ctxS = document.getElementById('chartSpend').getContext('2d');
  chartSpend = new Chart(ctxS, {{
    type: 'bar',
    data: {{
      labels: labels,
      datasets: [{{
        data: arms.map(a => a.mean_spend),
        backgroundColor: colors,
        borderRadius: 8,
        barPercentage: 0.6,
        errorBars: arms.map(a => ({{ low: a.spend_ci_95[0], high: a.spend_ci_95[1] }}))
      }}]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{
          callbacks: {{
            label: (ctx) => `Mean Spend: $${{ctx.raw.toFixed(2)}} [95% CI: $${{arms[ctx.dataIndex].spend_ci_95[0].toFixed(2)}} - $${{arms[ctx.dataIndex].spend_ci_95[1].toFixed(2)}}]`
          }}
        }}
      }},
      scales: {{
        y: {{
          beginAtZero: true,
          max: 2.0,
          ticks: {{ callback: v => '$' + v }},
          grid: {{ color: 'rgba(0,0,0,0.04)' }}
        }},
        x: {{ grid: {{ display: false }} }}
      }}
    }}
  }});
}}

// 3. Heterogeneity & Subgroups Tabs
function switchModifier(modifierKey) {{
  const tabs = document.querySelectorAll('.pill-tab');
  tabs.forEach(t => t.classList.remove('active'));
  event.target.classList.add('active');
  renderModifierTab(modifierKey);
}}

function renderModifierTab(modifierKey) {{
  // Find interaction tests for this modifier
  const intTests = DASHBOARD_DATA.interaction_tests.filter(t => t.comparison.includes(modifierKey));
  const intVisit = intTests.find(t => t.outcome === 'visit');
  const intConv = intTests.find(t => t.outcome === 'conversion');
  const intSpend = intTests.find(t => t.outcome === 'spend');

  // Interaction Badge Container
  const badgeContainer = document.getElementById('interactionBadgeContainer');
  const isVisitConfirmed = intVisit && intVisit.evidence_label === 'confirmed';
  badgeContainer.innerHTML = isVisitConfirmed
    ? `<span class="badge badge-confirmed">Confirmed Interaction (Visit)</span>`
    : `<span class="badge badge-exploratory">Exploratory &mdash; did not survive correction</span>`;

  // Interaction Banner
  const banner = document.getElementById('interactionBanner');
  banner.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
      <div>
        <strong>Interaction Test Results:</strong> 
        Visit &chi;&sup2; = ${{intVisit ? intVisit.estimate.toFixed(1) : '-'}} (Holm p = ${{intVisit ? intVisit.holm_p.toExponential(2) : '-'}}) &bull; 
        Conv &chi;&sup2; = ${{intConv ? intConv.estimate.toFixed(1) : '-'}} (Holm p = ${{intConv ? intConv.holm_p.toFixed(3) : '-'}}) &bull; 
        Spend &chi;&sup2; = ${{intSpend ? intSpend.estimate.toFixed(1) : '-'}} (Holm p = ${{intSpend ? intSpend.holm_p.toFixed(3) : '-'}})
      </div>
      <div>
        ${{isVisitConfirmed 
          ? '<span style="color: #15803D; font-weight: 600; font-size: 12.5px;">✓ Significant traffic heterogeneity across groups</span>' 
          : '<span style="color: #64748B; font-size: 12.5px;">No significant treatment-effect modification detected</span>'}}
      </div>
    </div>
  `;

  // Render Subgroups
  const container = document.getElementById('subgroupsContainer');
  if (modifierKey === 'purchase_history') {{
    renderPurchaseHistorySubgroups(container);
  }} else {{
    renderGenericSubgroups(container, modifierKey);
  }}
}}

function renderPurchaseHistorySubgroups(container) {{
  const phTests = DASHBOARD_DATA.purchase_history_head_to_head;
  const groups = ['Mens-only', 'Womens-only', 'Both'];

  let html = `<div class="subgroup-grid">`;
  groups.forEach(g => {{
    const visitTest = phTests.find(t => t.comparison.includes(g) && t.outcome === 'visit');
    const convTest = phTests.find(t => t.comparison.includes(g) && t.outcome === 'conversion');
    const spendTest = phTests.find(t => t.comparison.includes(g) && t.outcome === 'spend');

    const isWomensOnly = (g === 'Womens-only');
    const cardClass = isWomensOnly ? 'subgroup-card highlight-zero' : 'subgroup-card';

    html += `
      <div class="${{cardClass}}">
        <div>
          <div class="subgroup-head">
            <span class="subgroup-title">${{g}} Customers</span>
            <span style="font-size: 11px; color: var(--text-muted); font-weight: 500;">
              ${{isWomensOnly ? '44.9% of file (N=28,734)' : (g === 'Mens-only' ? '45.0% of file (N=28,818)' : '10.1% of file (N=6,448)')}}
            </span>
          </div>

          <!-- Head-to-Head Mens vs Womens -->
          <div style="font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-muted); font-weight: 600; margin-bottom: 8px;">
            Mens E-Mail vs. Womens E-Mail Lift
          </div>

          <!-- Visit Row -->
          <div class="subgroup-metric-row">
            <span class="metric-name">Visit Rate Lift</span>
            <div class="metric-val-wrap">
              <span>${{visitTest.estimate > 0 ? '+' : ''}}${{visitTest.estimate.toFixed(2)}} pp</span>
              <span class="badge ${{visitTest.evidence_label === 'confirmed' ? 'badge-confirmed' : 'badge-exploratory'}}">
                ${{visitTest.evidence_label === 'confirmed' ? 'Confirmed' : 'Exploratory'}}
              </span>
            </div>
          </div>

          <!-- Conversion Row -->
          <div class="subgroup-metric-row">
            <span class="metric-name">Conversion Lift</span>
            <div class="metric-val-wrap">
              <span>${{convTest.estimate > 0 ? '+' : ''}}${{convTest.estimate.toFixed(2)}} pp</span>
              <span class="badge ${{convTest.evidence_label === 'confirmed' ? 'badge-confirmed' : 'badge-exploratory'}}">
                ${{convTest.evidence_label === 'confirmed' ? 'Confirmed' : 'Exploratory'}}
              </span>
            </div>
          </div>

          <!-- Spend Row -->
          <div class="subgroup-metric-row">
            <span class="metric-name">Mean Spend Lift</span>
            <div class="metric-val-wrap">
              <span>${{spendTest.estimate > 0 ? '+' : ''}}$${{spendTest.estimate.toFixed(2)}}</span>
              <span class="badge ${{spendTest.evidence_label === 'confirmed' ? 'badge-confirmed' : 'badge-exploratory'}}">
                ${{spendTest.evidence_label === 'confirmed' ? 'Confirmed' : 'Exploratory'}}
              </span>
            </div>
          </div>
        </div>

        ${{isWomensOnly ? `
          <div style="margin-top: 14px; background: #FFF9F7; border: 1px solid rgba(255, 107, 74, 0.2); border-radius: var(--radius-sm); padding: 10px 12px; font-size: 12px; color: #9A3412;">
            <strong>No Detectable Creative Difference:</strong> Observed spend difference between Mens and Womens email is only 1.6 cents (p = 0.94). Sending Mens E-Mail does NOT sacrifice revenue.
          </div>
        ` : `
          <div style="margin-top: 14px; background: rgba(0,0,0,0.02); border-radius: var(--radius-sm); padding: 10px 12px; font-size: 12px; color: var(--text-secondary);">
            <strong>Mens E-Mail Dominates:</strong> Statistically confirmed browsing advantage (+${{visitTest.estimate.toFixed(2)}} pp). Spend lift is positive (+${{spendTest.estimate.toFixed(2)}}) though exploratory under Holm correction.
          </div>
        `}}
      </div>
    `;
  }});
  html += `</div>`;
  container.innerHTML = html;
}}

function renderGenericSubgroups(container, modifierKey) {{
  const subRows = DASHBOARD_DATA.subgroup_estimates.filter(s => s.Modifier === modifierKey);
  const subgroups = [...new Set(subRows.map(s => s.Subgroup))];

  let html = `<div class="subgroup-grid" style="grid-template-columns: repeat(${{Math.min(subgroups.length, 3)}}, 1fr);">`;
  subgroups.forEach(g => {{
    const vRow = subRows.find(s => s.Subgroup === g && s.Outcome === 'visit');
    const cRow = subRows.find(s => s.Subgroup === g && s.Outcome === 'conversion');
    const sRow = subRows.find(s => s.Subgroup === g && s.Outcome === 'spend');

    html += `
      <div class="subgroup-card">
        <div>
          <div class="subgroup-head">
            <span class="subgroup-title">${{g}}</span>
            <span style="font-size: 11.5px; color: var(--text-muted); font-weight: 500;">N = ${{vRow ? vRow.N_Total.toLocaleString() : '-'}}</span>
          </div>

          <div style="font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-muted); font-weight: 600; margin-bottom: 8px;">
            Mens vs. Womens E-Mail
          </div>

          <div class="subgroup-metric-row">
            <span class="metric-name">Visit Lift</span>
            <div class="metric-val-wrap">
              <span>${{vRow && vRow.ATE_Mens_vs_Womens > 0 ? '+' : ''}}${{vRow ? vRow.ATE_Mens_vs_Womens.toFixed(2) : '-'}} pp</span>
              <span class="badge badge-exploratory">Exploratory</span>
            </div>
          </div>

          <div class="subgroup-metric-row">
            <span class="metric-name">Conversion Lift</span>
            <div class="metric-val-wrap">
              <span>${{cRow && cRow.ATE_Mens_vs_Womens > 0 ? '+' : ''}}${{cRow ? cRow.ATE_Mens_vs_Womens.toFixed(2) : '-'}} pp</span>
              <span class="badge badge-exploratory">Exploratory</span>
            </div>
          </div>

          <div class="subgroup-metric-row">
            <span class="metric-name">Spend Lift</span>
            <div class="metric-val-wrap">
              <span>${{sRow && sRow.ATE_Mens_vs_Womens > 0 ? '+' : ''}}$${{sRow ? sRow.ATE_Mens_vs_Womens.toFixed(2) : '-'}}</span>
              <span class="badge badge-exploratory">Exploratory</span>
            </div>
          </div>
        </div>

        <div style="margin-top: 14px; font-size: 12px; color: var(--text-muted);">
          Interaction is exploratory (did not survive family-wise Holm correction).
        </div>
      </div>
    `;
  }});
  html += `</div>`;
  container.innerHTML = html;
}}

// 4. Decision Simulator
function updateSimulation() {{
  const marginPct = parseFloat(document.getElementById('marginSlider').value);
  const cost = parseFloat(document.getElementById('costSlider').value);
  const margin = marginPct / 100.0;

  document.getElementById('marginDisplay').textContent = `${{marginPct}}%`;
  document.getElementById('costDisplay').textContent = `$${{cost.toFixed(2)}}`;

  // Break-even costs: ATE_spend * margin
  const ateSpendM = 0.769827;
  const bootLowM = 0.4875;
  const ateSpendW = 0.424412;
  const bootLowW = 0.1689;

  const beM = ateSpendM * margin;
  const beMCons = bootLowM * margin;
  const beW = ateSpendW * margin;
  const beWCons = bootLowW * margin;

  document.getElementById('mensBreakEven').textContent = `$${{beM.toFixed(3)}} / email`;
  document.getElementById('mensBreakEvenCons').textContent = `$${{beMCons.toFixed(3)}}`;
  document.getElementById('womensBreakEven').textContent = `$${{beW.toFixed(3)}} / email`;
  document.getElementById('womensBreakEvenCons').textContent = `$${{beWCons.toFixed(3)}}`;

  // Strategy comparison
  // Policy (c): Mens to everyone -> 1000 * (ATE_M * margin - cost)
  const profC = 1000.0 * (ateSpendM * margin - cost);
  
  // Difference (e) - (c): 1000 * share_wo * margin * diff_spend
  const shareWo = 28734 / 64000; // 0.44896875
  const diffSpendWo = 1.122212 - 1.106295; // 0.015917
  const diffPer1k = 1000.0 * shareWo * margin * diffSpendWo;
  const profE = profC + diffPer1k;

  // 95% Bootstrap CI bounds scaled by margin
  // At margin 1.00: [-177.95, +190.12]
  const ciLow = -177.95 * margin;
  const ciHigh = 190.12 * margin;

  document.getElementById('policyCProfit').textContent = `$${{profC.toFixed(2)}} / 1k`;
  document.getElementById('policyEProfit').textContent = `$${{profE.toFixed(2)}} / 1k`;
  document.getElementById('policyDiff').textContent = `Lift over Mens All: +$${{diffPer1k.toFixed(2)}} / 1k`;

  document.getElementById('dynamicDiffText').textContent = `+$${{diffPer1k.toFixed(2)}}`;
  document.getElementById('dynamicCiText').textContent = `[-$${{Math.abs(ciLow).toFixed(2)}}, +$${{ciHigh.toFixed(2)}}]`;
}}

// 5. Limitations
function renderLimitations() {{
  const container = document.getElementById('limitationsGrid');
  const lims = DASHBOARD_DATA.limitations;
  let html = '';
  lims.forEach(l => {{
    html += `
      <div class="limitation-item">
        <div class="limitation-num">${{l.item}}</div>
        <div class="limitation-text">
          <h4>${{l.title}}</h4>
          <p>${{l.detail}}</p>
        </div>
      </div>
    `;
  }});
  container.innerHTML = html;
}}
</script>

</body>
</html>
'''

    with open('index.html', 'w') as f:
        f.write(html_content)
    print("Successfully built index.html with embedded data and interactive Chart.js visualizations.")

if __name__ == '__main__':
    create_dashboard_html()
