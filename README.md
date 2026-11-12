# Rent pricing tool

A small web tool that helps a landlord decide what monthly rent to list one house at.
It shows each rent source, combines them with a weighted median, widens the range when
sources disagree, and finds the list price with the best expected 12-month income.

**Status:** runs on PLACEHOLDER data (120 S Raleigh St is off market). Replace
`data/property.json` and `data/sources.json` with the live listing and confirmed comps.

## Run
    pip install -r requirements.txt
    uvicorn main:app --reload        # open http://localhost:8000
    pytest -q                        # 10 tests

## How the model works (model.py)
1. `normalize_sources`: asking rents discounted; comps adjusted for size, bedrooms, bathrooms
   (capped, and trusted less when heavily adjusted); weight = type x recency x similarity.
2. `reconcile`: weighted median; range from the weighted median absolute deviation
   (never narrower than 3%, and at least 8% with fewer than 3 sources); outliers flagged, not dropped.
3. `best_price`: daily lease chance = base_rate x exp(-sensitivity x (price/market - 1));
   expected vacant days = 1 / chance; income = rent x months occupied - leasing fee - vacant-day cost.

## Known limits
Base lease rate and price sensitivity are assumed, not fitted. Asking rents are discounted by an
assumed amount. One house, one snapshot, no backtest. Expected income uses expected days, not a full
distribution of outcomes.

## Deploy (one service)
Build: `pip install -r requirements.txt`  Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
Works on Render, Railway or Fly. Test a cold start before the walkthrough call.
