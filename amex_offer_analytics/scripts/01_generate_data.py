"""
01_generate_data.py
Generates a synthetic dataset: customers, merchants,
offers, and offer_exposures (the fact table — a card member is shown
an offer and may or may not redeem it).

"""

import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker

# ---------------- CONFIG ----------------
SEED = 42
N_CUSTOMERS = 5000
N_MERCHANTS = 150
N_OFFERS = 600
N_EXPOSURES = 60000
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

np.random.seed(SEED)
random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

os.makedirs(OUTPUT_DIR, exist_ok=True)

CATEGORIES = ["Dining", "Travel", "Grocery", "Retail", "Entertainment",
              "Electronics", "Fuel", "Health & Wellness"]
CATEGORY_APPEAL = {  # baseline redemption pull of each category
    "Dining": 0.85, "Grocery": 0.80, "Fuel": 0.70, "Retail": 0.60,
    "Entertainment": 0.55, "Health & Wellness": 0.50,
    "Travel": 0.45, "Electronics": 0.35,
}
INCOME_BRACKETS = ["Low", "Mid", "High", "Affluent"]
INCOME_WEIGHT = {"Low": 0.20, "Mid": 0.45, "High": 0.25, "Affluent": 0.10}
CARD_TYPES = ["Green", "Gold", "Platinum", "Centurion"]
OFFER_TYPES = ["Cashback", "Statement Credit", "Bonus Points", "Discount"]
REGIONS = ["North", "South", "East", "West", "Central"]


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


# ---------------------------------------------------------------
# 1. CUSTOMERS
# ---------------------------------------------------------------
print("Generating customers...")
customer_ids = [f"C{100000+i}" for i in range(N_CUSTOMERS)]
income = np.random.choice(INCOME_BRACKETS, size=N_CUSTOMERS,
                           p=[INCOME_WEIGHT[b] for b in INCOME_BRACKETS])
tenure_months = np.random.randint(1, 181, size=N_CUSTOMERS)
age = np.clip(np.random.normal(38, 11, size=N_CUSTOMERS).astype(int), 21, 75)
card_type = np.random.choice(CARD_TYPES, size=N_CUSTOMERS, p=[0.40, 0.35, 0.20, 0.05])

income_score_map = {"Low": 0.1, "Mid": 0.35, "High": 0.65, "Affluent": 0.9}
income_score = np.array([income_score_map[b] for b in income])
tenure_score = tenure_months / 180

# hidden "true" engagement propensity — drives redemption behavior realistically,
# NOT exported (Amex wouldn't hand this to an analyst; it's the thing we're
# trying to *infer* via segmentation)
propensity = np.clip(
    0.15 * income_score + 0.15 * tenure_score
    + np.random.normal(0, 0.18, N_CUSTOMERS) + 0.35,
    0.02, 0.98,
)

customers = pd.DataFrame({
    "customer_id": customer_ids,
    "age": age,
    "gender": np.random.choice(["M", "F"], size=N_CUSTOMERS, p=[0.52, 0.48]),
    "city": [fake.city() for _ in range(N_CUSTOMERS)],
    "income_bracket": income,
    "tenure_months": tenure_months,
    "card_type": card_type,
})
customers.to_csv(f"{OUTPUT_DIR}/customers.csv", index=False)
_propensity_lookup = dict(zip(customer_ids, propensity))

# ---------------------------------------------------------------
# 2. MERCHANTS
# ---------------------------------------------------------------
print("Generating merchants...")
merchant_ids = [f"M{2000+i}" for i in range(N_MERCHANTS)]
merchant_category = np.random.choice(CATEGORIES, size=N_MERCHANTS)
merchants = pd.DataFrame({
    "merchant_id": merchant_ids,
    "merchant_name": [fake.company() for _ in range(N_MERCHANTS)],
    "category": merchant_category,
    "region": np.random.choice(REGIONS, size=N_MERCHANTS),
})
merchants.to_csv(f"{OUTPUT_DIR}/merchants.csv", index=False)
merchant_category_lookup = dict(zip(merchant_ids, merchant_category))

# ---------------------------------------------------------------
# 3. OFFERS
# ---------------------------------------------------------------
print("Generating offers...")
offer_ids = [f"O{5000+i}" for i in range(N_OFFERS)]
offer_merchant = np.random.choice(merchant_ids, size=N_OFFERS)
offer_category = [merchant_category_lookup[m] for m in offer_merchant]
offer_type = np.random.choice(OFFER_TYPES, size=N_OFFERS)
discount_pct = np.random.choice([5, 10, 15, 20, 25, 30], size=N_OFFERS)
min_spend = np.random.choice([0, 500, 1000, 2000, 5000], size=N_OFFERS,
                              p=[0.35, 0.25, 0.20, 0.15, 0.05])

start_base = datetime(2024, 1, 1)
start_dates = [start_base + timedelta(days=int(d))
               for d in np.random.randint(0, 500, N_OFFERS)]
offer_length = np.random.choice([15, 30, 45, 60, 90], size=N_OFFERS)
end_dates = [s + timedelta(days=int(l)) for s, l in zip(start_dates, offer_length)]

offers = pd.DataFrame({
    "offer_id": offer_ids,
    "merchant_id": offer_merchant,
    "category": offer_category,
    "offer_type": offer_type,
    "discount_pct": discount_pct,
    "min_spend": min_spend,
    "start_date": [d.date() for d in start_dates],
    "end_date": [d.date() for d in end_dates],
})
offers.to_csv(f"{OUTPUT_DIR}/offers.csv", index=False)
offer_lookup = offers.set_index("offer_id")

# ---------------------------------------------------------------
# 4. OFFER EXPOSURES (fact table)
# ---------------------------------------------------------------
print("Generating offer exposures (this is the largest table)...")
exp_customer = np.random.choice(customer_ids, size=N_EXPOSURES)
exp_offer = np.random.choice(offer_ids, size=N_EXPOSURES)
income_lookup = dict(zip(customer_ids, income))
income_mult = {"Low": 0.7, "Mid": 1.0, "High": 1.6, "Affluent": 2.4}

rows = []
for i in range(N_EXPOSURES):
    cust = exp_customer[i]
    off = exp_offer[i]
    off_row = offer_lookup.loc[off]
    cat = off_row["category"]
    disc = off_row["discount_pct"]
    min_sp = off_row["min_spend"]

    prop = _propensity_lookup[cust]
    appeal = CATEGORY_APPEAL[cat]

    z = (-3.3 + 2.6 * prop + 1.4 * appeal + 0.02 * disc - 0.00035 * min_sp)
    p_redeem = sigmoid(z)
    redeemed = np.random.rand() < p_redeem

    exposure_date = start_base + timedelta(days=int(np.random.randint(0, 560)))

    if redeemed:
        redemption_lag = np.random.randint(1, 30)
        redemption_date = exposure_date + timedelta(days=int(redemption_lag))
        base_spend = max(min_sp, 300)
        spend_amount = round(
            base_spend * income_mult[income_lookup[cust]] * np.random.uniform(1.0, 2.2), 2
        )
    else:
        redemption_date = None
        spend_amount = 0.0

    rows.append((
        f"E{1000000+i}", cust, off, off_row["merchant_id"], cat,
        exposure_date.date(), int(redeemed), spend_amount,
        redemption_date.date() if redemption_date else None,
    ))

    if (i + 1) % 15000 == 0:
        print(f"  ...{i+1}/{N_EXPOSURES} exposures generated")

exposures = pd.DataFrame(rows, columns=[
    "exposure_id", "customer_id", "offer_id", "merchant_id", "category",
    "exposure_date", "redeemed", "spend_amount", "redemption_date",
])
exposures.to_csv(f"{OUTPUT_DIR}/offer_exposures.csv", index=False)

print("\nDone. Files written to ./data/")
print(f"  customers.csv         : {len(customers):,} rows")
print(f"  merchants.csv          : {len(merchants):,} rows")
print(f"  offers.csv             : {len(offers):,} rows")
print(f"  offer_exposures.csv    : {len(exposures):,} rows")
print(f"  Overall redemption rate: {exposures['redeemed'].mean():.1%}")
