# Rent Plan

A small web tool that helps one landlord make one decision about one house: **what to list the rent at,
and what to do if it does not lease** ("list at $X; if not leased by day N, cut to $Y").

Live example: 18674 E 40th Pl, Denver, CO 80249 (3 bd / 2 ba / 1,626 sqft, listed at $2,800 on 2026-11-11).

## What it does
- Shows every rent source (listing, platform estimates, nearby comps), how each was adjusted, and how much it counts.
- Combines them into a market estimate with a range, and says how much the sources disagree.
- Finds the list price with the best expected 12-month income, and a price-cut plan.
- Shows how the answer moves if the assumptions are wrong, and what the tool cannot know.
- The landlord can edit the house (beds, baths, sqft, ask), switch sources on or off, and add his own sources.

## What it does not do
- It does not look anything up. The address is a label. Sources are typed into `data/houses/*.json`
  (the example houses) or added on the page.
- It does not know leased rents, days on market, or the house's condition.
- It has not been checked against real outcomes.

## Run
    pip install -r requirements.txt
    uvicorn main:app --reload        # open http://localhost:8000
    pytest -q                        # 26 tests

## How the model works (model.py, no randomness, no ML)
1. `normalize_sources`: asking rents are discounted (3%, assumed); asking comps are adjusted for size,
   bedrooms and bathrooms (adjustments capped at 25%, and trusted less when large);
   weight = type x recency x similarity. Estimates and leased comps are not adjusted for size or layout.
2. `reconcile`: weighted median; range from the weighted median absolute deviation (never narrower than
   3% of the estimate, at least 8% with fewer than 3 sources); outliers are flagged, not dropped;
   disagreement is rated low / medium / high from the spread.
3. `evaluate` / `best_price`: daily lease chance = base rate x exp(-sensitivity x (price/market - 1));
   expected vacant days = 1 / chance; income = rent x months occupied - leasing fee - vacant-day cost.
4. `plan_income` / `best_plan`: simulates each vacant day for "list at X, cut to Y on day N", averaged over
   a low / middle / high market (25% / 50% / 25%, assumed), and compares it with the best single price.
5. `recommend` runs the steps above and six sensitivity checks.

## Tech stack
| Piece | Why |
|---|---|
| Python | The model is plain functions with no randomness, so every number can be checked by hand. |
| FastAPI | One small service that serves the page and runs the model; automatic `/docs` page for trying the API. |
| Pydantic v2 | Checks every request (types, ranges, allowed source types) before the model runs. It validates shape, not truth. |
| HTML, CSS and JavaScript (no framework) | One page, no build step to learn or debug. |
| JSON files in `data/houses/` | One house, so no database. Every source carries a URL and access date, so each number can be audited. |
| pytest and GitHub Actions | 26 tests (hand-computed cases, edge cases, API validation) run on every push. |
| Render (free tier) | Public URL for the deployed tool. |

Left out on purpose: database, cache, accounts, an LLM, a frontend framework. One user and one house do not need them.

## Documents
- `docs/Rent-Tool-Summary.pdf` one-page written summary: the decision and reasoning, how conflicting sources were handled, what could not be obtained.
- `docs/ai-log.md` record of AI use, including disagreements and bugs.

## Known limits
- Base lease rate, price sensitivity, the 3% discount, the source weights and the 25/50/25 market cases
  are assumptions, not fitted to data. Public data on days-to-lease for houses is thin.
- One house, one snapshot, no backtest, so accuracy cannot be measured.
- Market reports mostly describe apartments, so they are not used for the rent level.
- The Denver Assessor (county) record is not entered yet. HUD fair market rent is entered and used as a sanity check.

## Files
- `model.py` the model; `main.py` FastAPI app (`/api/defaults`, `/api/recommend`); `static/index.html` the page
- `data/houses/*.json` one file per example house (facts + sources, each with a URL and access date); a "My own house" option starts blank
- `test_model.py` model tests; `test_api.py` checks that every example house loads and produces a plan

## Deploy (one service)
Build: `pip install -r requirements.txt`   Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
Runs on Render's free tier. The first request after idle can take about a minute.
