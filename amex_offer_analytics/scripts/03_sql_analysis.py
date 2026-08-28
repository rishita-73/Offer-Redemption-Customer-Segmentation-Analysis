"""
03_sql_analysis.py
Runs the core analysis queries against amex_offers.db and exports each result as a CSV in
outputs/sql_results/ 
"""

import os
import sqlite3

import pandas as pd

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DB_PATH = os.path.join(BASE_DIR, "amex_offers.db")
OUT_DIR = os.path.join(BASE_DIR, "outputs", "sql_results")
os.makedirs(OUT_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)

queries = {
    "overall_adoption_rate": """
        SELECT COUNT(*) AS total_exposures, SUM(redeemed) AS total_redemptions,
               ROUND(100.0*SUM(redeemed)/COUNT(*),2) AS adoption_rate_pct
        FROM offer_exposures;
    """,
    "redemption_by_category": """
        SELECT category, COUNT(*) AS exposures, SUM(redeemed) AS redemptions,
               ROUND(100.0*SUM(redeemed)/COUNT(*),2) AS redemption_rate_pct,
               ROUND(SUM(spend_amount),2) AS total_revenue,
               ROUND(SUM(spend_amount)/NULLIF(SUM(redeemed),0),2) AS avg_spend_per_redemption
        FROM offer_exposures GROUP BY category ORDER BY redemption_rate_pct DESC;
    """,
    "top_offers": """
        SELECT o.offer_id, m.merchant_name, o.category, o.offer_type, o.discount_pct,
               COUNT(e.exposure_id) AS exposures, SUM(e.redeemed) AS redemptions,
               ROUND(100.0*SUM(e.redeemed)/COUNT(e.exposure_id),2) AS redemption_rate_pct
        FROM offer_exposures e
        JOIN offers o ON e.offer_id = o.offer_id
        JOIN merchants m ON o.merchant_id = m.merchant_id
        GROUP BY o.offer_id HAVING COUNT(e.exposure_id) >= 50
        ORDER BY redemption_rate_pct DESC LIMIT 10;
    """,
    "redemption_by_discount_tier": """
        SELECT CASE WHEN discount_pct<=10 THEN '5-10%' WHEN discount_pct<=20 THEN '15-20%' ELSE '25-30%' END AS discount_tier,
               COUNT(*) AS exposures, ROUND(100.0*SUM(redeemed)/COUNT(*),2) AS redemption_rate_pct
        FROM offer_exposures e JOIN offers o ON e.offer_id=o.offer_id
        GROUP BY discount_tier ORDER BY discount_tier;
    """,
    "redemption_by_income_card": """
        SELECT c.income_bracket, c.card_type, COUNT(*) AS exposures,
               ROUND(100.0*SUM(e.redeemed)/COUNT(*),2) AS redemption_rate_pct,
               ROUND(SUM(e.spend_amount),2) AS total_revenue
        FROM offer_exposures e JOIN customers c ON e.customer_id=c.customer_id
        GROUP BY c.income_bracket, c.card_type ORDER BY redemption_rate_pct DESC;
    """,
    "monthly_trend": """
        SELECT strftime('%Y-%m', exposure_date) AS month, COUNT(*) AS exposures,
               SUM(redeemed) AS redemptions, ROUND(100.0*SUM(redeemed)/COUNT(*),2) AS redemption_rate_pct
        FROM offer_exposures GROUP BY month ORDER BY month;
    """,
}

for name, q in queries.items():
    df = pd.read_sql_query(q, conn)
    df.to_csv(f"{OUT_DIR}/{name}.csv", index=False)
    print(f"\n=== {name} ===")
    print(df.to_string(index=False))

conn.close()
print(f"\nAll results exported to {OUT_DIR}/ (import these into Power BI)")
