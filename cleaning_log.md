# Data Cleaning and Preparation Log

**Source File**: `hillstrom_email_analytics.csv` (Untouched, MD5 preserved)  
**Destination File**: `hillstrom_cleaned.csv`  
**Execution Timestamp**: 2026-09-28  
**Total Records**: 64,000 (0 rows dropped)  
**Total Columns**: 15 (original 12 + 3 treatment indicators)

---

## Log of Modifications Made

1. **Typo Correction in `zip_code`**:
   - Replaced label `'Surburban'` with `'Suburban'`.
   - Affected rows: 28,776.
   - Distinct values before: `['Surburban', 'Rural', 'Urban']`
   - Distinct values after: `['Suburban', 'Rural', 'Urban']`

2. **Row Integrity Preservation**:
   - All 64,000 rows were retained.
   - All 6,562 exact duplicate rows were explicitly preserved as legitimate independent customer records lacking an explicit customer ID.

3. **No Outcome Alterations**:
   - Zero spend values were modified, capped, or imputed. All continuous dollar figures remain identical to raw data.
   - Outcomes `visit`, `conversion`, and `spend` remain completely unmodified.

4. **Treatment Encodings Created**:
   - `treatment_arm`: Categorical column with ordered levels setting `'No E-Mail'` as the reference / control level, followed by `'Mens E-Mail'` and `'Womens E-Mail'`.
   - `treatment_mens`: Binary dummy variable (`1` if `segment == 'Mens E-Mail'`, `0` otherwise).
   - `treatment_womens`: Binary dummy variable (`1` if `segment == 'Womens E-Mail'`, `0` otherwise).
   - Control condition (`'No E-Mail'`) is represented by `treatment_mens == 0` and `treatment_womens == 0`.
