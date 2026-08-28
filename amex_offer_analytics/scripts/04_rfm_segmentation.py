"""
04_rfm_segmentation.py
Builds RFM (Recency, Frequency, Monetary) features per customer from
offer_exposures, standardizes them, and runs K-Means to produce
business-readable customer segments.

"""

import os
import sqlite3

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DB_PATH = os.path.join(BASE_DIR, "amex_offers.db")
OUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
exposures = pd.read_sql_query("SELECT * FROM offer_exposures", conn)
customers = pd.read_sql_query("SELECT * FROM customers", conn)
conn.close()

exposures["exposure_date"] = pd.to_datetime(exposures["exposure_date"])
exposures["redemption_date"] = pd.to_datetime(exposures["redemption_date"])

snapshot_date = exposures["exposure_date"].max() + pd.Timedelta(days=1)
redeemed = exposures[exposures["redeemed"] == 1]

rfm = redeemed.groupby("customer_id").agg(
    recency_days=("redemption_date", lambda x: (snapshot_date - x.max()).days),
    frequency=("redeemed", "sum"),
    monetary=("spend_amount", "sum"),
).reset_index()

# customers with zero redemptions never appear above — add them back with worst-case RFM
all_customers = customers[["customer_id"]].copy()
rfm = all_customers.merge(rfm, on="customer_id", how="left")
worst_case_recency = (snapshot_date - exposures["exposure_date"].min()).days
rfm["recency_days"] = rfm["recency_days"].fillna(worst_case_recency)
rfm["frequency"] = rfm["frequency"].fillna(0)
rfm["monetary"] = rfm["monetary"].fillna(0)

# ---- K-Means clustering ----
features = rfm[["recency_days", "frequency", "monetary"]].copy()
features["frequency"] = np.log1p(features["frequency"])   # reduce skew (standard RFM practice)
features["monetary"] = np.log1p(features["monetary"])

scaler = StandardScaler()
X = scaler.fit_transform(features)

kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
rfm["cluster"] = kmeans.fit_predict(X)

# ---- Label clusters by business meaning, using centroid stats ----
summary = rfm.groupby("cluster")[["recency_days", "frequency", "monetary"]].mean().round(1)
print("Cluster centroids (raw units):\n", summary)

summary["score"] = (
    summary["frequency"].rank() + summary["monetary"].rank() - summary["recency_days"].rank()
)
ranked = summary.sort_values("score", ascending=False).index.tolist()

labels = {
    ranked[0]: "Champions (high-value, engaged)",
    ranked[1]: "Steady Redeemers",
    ranked[2]: "At-Risk / Lapsing",
    ranked[3]: "Low-Engagement / New",
}
rfm["segment"] = rfm["cluster"].map(labels)

final = rfm.merge(customers, on="customer_id")
final.to_csv(f"{OUT_DIR}/segmented_customers.csv", index=False)

print("\nSegment sizes:")
print(final["segment"].value_counts())
print(f"\nSaved: {OUT_DIR}/segmented_customers.csv")
