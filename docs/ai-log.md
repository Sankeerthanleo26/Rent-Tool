# AI usage log

Format: what I asked, what the AI proposed, what I decided, why.

## 2026-11-11
- **Scope.** AI first proposed a React frontend, Monte Carlo simulation and an LLM. I decided on a
  five-hour scope with no LLM: Oakwood is judging thought process, and I want to explain every part.
- **Listing.** AI proposed listings from cached search pages, one of them off market. Rule adopted:
  a person confirms a listing is live before it is used.
- **Disagreement with the AI's first model (AI found it, I should explain it).** A 950 sqft comp
  was scaled up to 3,543 per month for size, which is not credible. Fix: cap adjustments at 25% and
  trust heavily adjusted comps less (test added).
- **Test failures.** Two tests failed on first run because the tests were wrong, not the model
  (a median that did not move; a boundary of exactly 0.5). Fixed the tests, kept the model.
- TODO (me): add points where I disagreed with the AI and why. Export the full chat as a backup.

## Switched subject property to 18674 E 40th Pl (2026-11-11)
- Picked by the user from a live HotPads link after earlier candidates (2338 Lowell Blvd, 3863 S Dallas St) could not be confirmed as live listings, and a link to a single-room listing was rejected because its $900 was a per-room rent.
- Conflicts found: Trulia lists 2 baths and says $2,800 includes required monthly fees; HotPads shows $2,800 base rent. Two nearby listings were turned off by default because availability or size was unclear (20000 E 40th Pl shows 2,890 sqft in the text but 1,736 in the title).
- Decision: count the subject listing once (HotPads and Trulia show the same number), and count 4094 Malta St once (its ForRent reading of 2,720 is available but off by default).
