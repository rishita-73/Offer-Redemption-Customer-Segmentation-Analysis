"""
05_visualize.py
Generates the core charts for the project: redemption rate by category,
customer segment distribution, RFM view, and revenue by segment.

"""

import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
OUT_DIR = os.path.join(BASE_DIR, "outputs", "charts")
os.makedirs(OUT_DIR, exist_ok=True)
sns.set_theme(style="whitegrid")

# 1. Redemption rate by category
cat = pd.read_csv(os.path.join(BASE_DIR, "outputs", "sql_results", "redemption_by_category.csv"))
plt.figure(figsize=(8, 5))
sns.barplot(data=cat.sort_values("redemption_rate_pct", ascending=False),
            x="redemption_rate_pct", y="category", hue="category",
            palette="Blues_r", legend=False)
plt.title("Offer Redemption Rate by Merchant Category")
plt.xlabel("Redemption Rate (%)")
plt.ylabel("")
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/redemption_rate_by_category.png", dpi=150)
plt.close()

# 2. Segment distribution
seg = pd.read_csv(os.path.join(BASE_DIR, "outputs", "segmented_customers.csv"))
plt.figure(figsize=(7, 5))
order = seg["segment"].value_counts().index
sns.countplot(data=seg, y="segment", order=order, hue="segment",
              palette="viridis", legend=False)
plt.title("Customer Segment Distribution")
plt.xlabel("Number of Customers")
plt.ylabel("")
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/segment_distribution.png", dpi=150)
plt.close()

# 3. RFM scatter (frequency vs monetary, colored by segment)
plt.figure(figsize=(8, 6))
sns.scatterplot(data=seg, x="frequency", y="monetary", hue="segment", alpha=0.6, palette="viridis")
plt.title("Customer Segments: Frequency vs Monetary Value")
plt.xlabel("Redemption Frequency")
plt.ylabel("Total Redeemed Spend")
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/rfm_scatter.png", dpi=150)
plt.close()

# 4. Revenue by segment
rev_by_seg = seg.groupby("segment")["monetary"].sum().sort_values(ascending=False)
plt.figure(figsize=(7, 5))
rev_by_seg.plot(kind="barh", color=sns.color_palette("viridis", len(rev_by_seg)))
plt.title("Total Redeemed Revenue by Segment")
plt.xlabel("Total Revenue")
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/revenue_by_segment.png", dpi=150)
plt.close()

print(f"Charts saved to {OUT_DIR}/")
