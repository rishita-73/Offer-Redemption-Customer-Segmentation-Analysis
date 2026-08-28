-- ============================================================
-- Amex Offers Analytics — Core SQL Queries
-- Target: amex_offers.db (SQLite) — created by 02_load_to_sql.py
-- These are the same queries 03_sql_analysis.py runs and exports;
-- kept here as a clean, standalone reference for your portfolio/interview.
-- ============================================================

-- 1. Overall offer adoption (redemption) rate
SELECT
    COUNT(*)                                   AS total_exposures,
    SUM(redeemed)                              AS total_redemptions,
    ROUND(100.0 * SUM(redeemed) / COUNT(*), 2) AS adoption_rate_pct
FROM offer_exposures;


-- 2. Redemption rate and revenue by merchant category
SELECT
    category,
    COUNT(*)                                              AS exposures,
    SUM(redeemed)                                         AS redemptions,
    ROUND(100.0 * SUM(redeemed) / COUNT(*), 2)             AS redemption_rate_pct,
    ROUND(SUM(spend_amount), 2)                           AS total_revenue,
    ROUND(SUM(spend_amount) / NULLIF(SUM(redeemed), 0), 2) AS avg_spend_per_redemption
FROM offer_exposures
GROUP BY category
ORDER BY redemption_rate_pct DESC;


-- 3. Top 10 performing offers (min 50 exposures, to avoid small-sample noise)
SELECT
    o.offer_id,
    m.merchant_name,
    o.category,
    o.offer_type,
    o.discount_pct,
    COUNT(e.exposure_id)                                     AS exposures,
    SUM(e.redeemed)                                          AS redemptions,
    ROUND(100.0 * SUM(e.redeemed) / COUNT(e.exposure_id), 2) AS redemption_rate_pct
FROM offer_exposures e
JOIN offers o    ON e.offer_id = o.offer_id
JOIN merchants m ON o.merchant_id = m.merchant_id
GROUP BY o.offer_id
HAVING COUNT(e.exposure_id) >= 50
ORDER BY redemption_rate_pct DESC
LIMIT 10;


-- 4. Redemption rate by discount tier — does a bigger discount drive more redemptions?
SELECT
    CASE
        WHEN discount_pct <= 10 THEN '5-10%'
        WHEN discount_pct <= 20 THEN '15-20%'
        ELSE '25-30%'
    END                                         AS discount_tier,
    COUNT(*)                                    AS exposures,
    ROUND(100.0 * SUM(redeemed) / COUNT(*), 2)  AS redemption_rate_pct
FROM offer_exposures e
JOIN offers o ON e.offer_id = o.offer_id
GROUP BY discount_tier
ORDER BY discount_tier;


-- 5. Redemption rate by customer income bracket & card type
SELECT
    c.income_bracket,
    c.card_type,
    COUNT(*)                                    AS exposures,
    ROUND(100.0 * SUM(e.redeemed) / COUNT(*), 2) AS redemption_rate_pct,
    ROUND(SUM(e.spend_amount), 2)               AS total_revenue
FROM offer_exposures e
JOIN customers c ON e.customer_id = c.customer_id
GROUP BY c.income_bracket, c.card_type
ORDER BY redemption_rate_pct DESC;


-- 6. Customer-level redemption frequency distribution
SELECT
    redemption_count,
    COUNT(*) AS num_customers
FROM (
    SELECT customer_id, SUM(redeemed) AS redemption_count
    FROM offer_exposures
    GROUP BY customer_id
) t
GROUP BY redemption_count
ORDER BY redemption_count;


-- 7. Monthly redemption trend
SELECT
    strftime('%Y-%m', exposure_date)             AS month,
    COUNT(*)                                     AS exposures,
    SUM(redeemed)                                AS redemptions,
    ROUND(100.0 * SUM(redeemed) / COUNT(*), 2)   AS redemption_rate_pct
FROM offer_exposures
GROUP BY month
ORDER BY month;
