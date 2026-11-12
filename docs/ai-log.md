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
