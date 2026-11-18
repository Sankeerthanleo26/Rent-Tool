# Rent Plan: one-page summary

**Property:** 18674 E 40th Pl, Denver, CO 80249 (3 bd, 2 ba, 1,626 sq ft), listed at $2,800 on 2026-11-11.
**Decision:** what monthly rent should this one landlord list the house at, and what should the plan be if it does not lease?

## Why this decision
A landlord with one house has no portfolio to absorb an empty month. Priced too high, the house sits empty while taxes, insurance and utilities keep running. Priced too low, the landlord loses revenue for the whole 12-month lease. It is the first decision at listing time, and the others (pets, bundled services, lease length) depend on it or need private data that no public source supplies. I judged that a small landlord cares first about filling the house; that is my reasoning, not a proven fact.

## What the tool says (default assumptions)
- Market estimate: **$2,716 a month, range $2,612 to $2,820**, from five sources that agree closely (spread about 7%).
- HUD cross-check: the FY2027 fair market rent for a 3-bedroom in the Denver metro is $2,846; the estimate is about 95% of it, inside the plausible band. HUD's figure is a voucher benchmark that includes utilities, so it is a sanity check only, not a source of the rent.
- Best single list price: about **$2,743**, against the current $2,800 ask.
- Best price-cut plan: start near $2,770 and cut about 4% (to about $2,660) on day 45. It beats the best single price by only about **$20 a year**, so for this house a single price is nearly as good. I report that instead of hiding it.

## How conflicting sources were handled
- **Base rent versus all-in:** HotPads shows $2,800 as base rent; Trulia says $2,800 includes required monthly fees. Flagged on the page; what the owner nets is unknown.
- **Same house, two sites:** the subject listing is counted once. 4094 Malta St reads $2,820 on one site and $2,720 on another; one reading is counted, the other is off by default and can be switched on.
- **Conflicting sizes:** 20000 E 40th Pl shows 2,890 sq ft in the text and 1,736 in the title, so it is off by default. A listing whose page says "check back soon" is also off.
- **Different sizes and layouts:** asking comps are adjusted for size and rooms, capped at 25%, and trusted less the more they were adjusted.
- **Asking versus achieved:** asking rents are cut by an assumed 3%.
- **Outliers** are flagged, never silently dropped. The range widens when sources disagree.
- **Stale data:** a cached search result said the house was off market; the live page showed it for rent, so a person confirms every listing is live before it is used.

## What I needed but could not get
- Leased (achieved) rents, days on market and price histories for houses; only asking rents are public.
- The house's condition, the landlord's real costs, and demand in a given week.
- Distance from each comp (not measured, so comps get a default similarity).
- The Denver Assessor record is not entered yet, so the tool cannot check the listing's square footage, beds and baths against the county.

## Limits
The base lease rate, price sensitivity, the 3% discount, the source weights and the 25/50/25 market cases are assumptions, not fitted to data. It is one house at one moment, with no backtest, so accuracy cannot be measured. Market reports mostly describe apartments, so they are not used for the rent level. The tool recommends a number; the landlord decides.
