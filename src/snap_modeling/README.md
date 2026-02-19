# District-Level SNAP Political Signal Modeling

## Overview

This module implements the predictive modeling framework described in:

"Mathematical Analysis of SNAP: Initial Findings"  
Thoshan Omprakash  
National Center for Supercomputing Applications | Policy Design Lab

The purpose of this analysis is to evaluate whether measurable economic characteristics of a congressional district are associated with political representation.

Specifically, this module models whether:

- SNAP participation rate
- Median household income (log-adjusted)

contain predictive signal for whether a congressional district elects a Democratic or Republican representative.

This implementation operationalizes the modeling framework described in the formal report.

---

## Research Objective

We test whether district-level economic variables contain meaningful political signal.

Target variable:
- 1 → Democratic representation
- 0 → Republican representation

Model structure (logistic regression form):

P(Democrat) = 1 / (1 + exp(-(β0 + β1·SNAP% + β2·log_income)))

Where:
- SNAP% = percentage of households receiving SNAP
- log_income = log(1 + median household income)

Performance is evaluated using ROC-AUC to measure discriminatory ability.

---

## Data Inputs

### 1. SNAP District Dataset

File location:

data/cat-snap-congressional-district-data-export.xlsx

Required columns:
- `fipscd`
- `hh_snap_pct`
- `hh_snap`
- `hh_total`
- `medhhinc`

### 2. Congressional District Party Labels

File location:

data/NTAD_Congressional_Districts_1009129779752246747.csv

Required columns:
- `STATEFP`
- `DISTRICT`
- `PARTY`

Only districts where PARTY ∈ {D, R} are retained.

---

## Data Processing

### District Identifier Construction

Both datasets are aligned using:

fipscd = STATEFP (2 digits) + DISTRICT (2 digits)

An inner merge ensures only districts present in both datasets are modeled.

A validation assertion confirms expected merge size (>400 districts).

---

## Feature Engineering

Income is log-transformed:

log_medhhinc = log(1 + medhhinc)

This transformation:
- Reduces influence of extreme high-income districts
- Improves numerical stability
- Produces a more balanced distribution
- Allows the model to focus on proportional economic differences

Model input features:
- `hh_snap_pct`
- `log_medhhinc`

---

## Model Framework

Two models are trained:

### Logistic Regression (Primary Model)
- Standardized features
- Maximum likelihood estimation
- Outputs probability of Democratic alignment

### Random Forest (Structural Consistency Check)
- 300 estimators
- Depth constraint
- Minimum leaf size constraint

Similar performance between the two models indicates structural consistency in the relationship between economic variables and party alignment.

---

## Evaluation Strategy

Evaluation includes:

- Train/test split (stratified)
- Accuracy
- Precision
- Recall
- ROC-AUC
- Full classification report
- 5-fold Stratified Cross-Validation (ROC-AUC)

ROC-AUC interpretation:

- 0.50 → random guessing
- 1.00 → perfect separation

Observed performance:
- Test ROC-AUC ≈ 0.81
- Cross-validated ROC-AUC ≈ 0.84

This indicates that the model correctly ranks a randomly selected Democratic district higher than a randomly selected Republican district approximately 84% of the time.

---

## Environment Setup

Python 3.9+

Install dependencies:

pip install pandas numpy scikit-learn openpyxl

---

## Running the Module

From repository root:

python src/snap_modeling/snap_party_prediction.py

Ensure file paths are repo-relative:

pd.read_excel("data/cat-snap-congressional-district-data-export.xlsx")
pd.read_csv("data/NTAD_Congressional_Districts_1009129779752246747.csv")

---

## Limitations

- Binary party classification only (D vs R)
- Cross-sectional (single time snapshot)
- Limited feature set (two primary variables)
- Does not persist trained model artifacts
- No temporal alignment verification between datasets

---

## Expansion Opportunities

Future extensions may include:

- Education attainment variables
- Race and ethnicity composition
- Age structure metrics
- Poverty and unemployment rates
- SNAP growth trends over time
- Urban vs rural controls
- Multi-year modeling
- Model persistence and deployment

---

## Relationship to Ingestion Pipeline

This module is exploratory and analytical.

It depends on structured district-level datasets produced via ingestion but does not modify ingestion logic or write outputs back to ingestion.

It is designed to evaluate structural socioeconomic signal at the congressional district level.
