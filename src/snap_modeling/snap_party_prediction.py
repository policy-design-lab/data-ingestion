
# Imports

import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    roc_auc_score,
    classification_report
)



#Load Data

snap_df = pd.read_excel("data/cat-snap-congressional-district-data-export.xlsx")

party_df = pd.read_csv("data/NTAD_Congressional_Districts_1009129779752246747.csv")



# Political Party labels

party_df = party_df[party_df["PARTY"].isin(["D", "R"])]

party_df["party_win"] = party_df["PARTY"].map({
    "D": 1,
    "R": 0
})



# Political Party fipscd 


party_df["STATEFP"] = party_df["STATEFP"].astype(int).astype(str).str.zfill(2)


party_df["DISTRICT"] = party_df["DISTRICT"].astype(int).astype(str).str.zfill(2)


party_df["fipscd"] = party_df["STATEFP"] + party_df["DISTRICT"]
party_df["fipscd"] = party_df["fipscd"].astype(int)


# SNAP fipscd

snap_df["fipscd"] = snap_df["fipscd"].astype(int)



# Debugging

print("SNAP fipscd sample:", snap_df["fipscd"].head(5).tolist())
print("PARTY fipscd sample:", party_df["fipscd"].head(5).tolist())

common = set(snap_df["fipscd"]).intersection(set(party_df["fipscd"]))
print("Common fipscd count:", len(common))



# Fipscode Merge

df = snap_df.merge(
    party_df[["fipscd", "party_win"]],
    on="fipscd",
    how="inner"
)

print("Merged districts:", df.shape[0])
assert df.shape[0] > 400, "Merge failed — check fipscd construction"



#Feature Selection

feature_cols = [
    "hh_snap_pct",
    "hh_snap",
    "hh_total",
    "medhhinc"
]

df = df.dropna(subset=feature_cols + ["party_win"])



# Feature Engineering

df["log_medhhinc"] = np.log1p(df["medhhinc"])



#Feature Matrix & Target

X = df[
    [
        "hh_snap_pct",
        "log_medhhinc"
    ]
]

y = df["party_win"]



# Train / Test Split

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.25,
    stratify=y,
    random_state=42
)



# Logistic Regression

log_reg = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", LogisticRegression(max_iter=1000))
])

log_reg.fit(X_train, y_train)

y_pred = log_reg.predict(X_test)
y_prob = log_reg.predict_proba(X_test)[:, 1]

print("\nLogistic Regression")
print("Accuracy:", accuracy_score(y_test, y_pred))
print("Precision:", precision_score(y_test, y_pred))
print("Recall:", recall_score(y_test, y_pred))
print("ROC-AUC:", roc_auc_score(y_test, y_prob))
print(classification_report(y_test, y_pred))



# 13. Random Forest

rf = RandomForestClassifier(
    n_estimators=300,
    max_depth=6,
    min_samples_leaf=10,
    random_state=42
)

rf.fit(X_train, y_train)

rf_pred = rf.predict(X_test)
rf_prob = rf.predict_proba(X_test)[:, 1]

print("\nRandom Forest")
print("Accuracy:", accuracy_score(y_test, rf_pred))
print("Precision:", precision_score(y_test, rf_pred))
print("Recall:", recall_score(y_test, rf_pred))
print("ROC-AUC:", roc_auc_score(y_test, rf_prob))



# 14. Cross-Validation

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

cv_auc = cross_val_score(
    log_reg,
    X,
    y,
    cv=cv,
    scoring="roc_auc"
)

print("\nCV ROC-AUC scores:", cv_auc)
print("Mean CV ROC-AUC:", cv_auc.mean())




