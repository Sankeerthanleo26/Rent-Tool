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

## Price-cut plan (2026-11-12)
- Chosen decision: "what do I list at, and what is my plan if it does not lease?"
- My first idea was that a cut rule would clearly beat a single price. Testing showed that with a constant daily lease chance the cut adds almost nothing, because waiting teaches you nothing. The cut only has value if the market is uncertain, so the plan averages over low/middle/high market cases taken from the reconciled range.
- Result for this house: the sources agree closely, so the gain from the cut rule is only about $20 a year; with a deliberately wide range it is $150 to $500. This is reported on the page instead of hiding it.
- The 25/50/25 weights on the market cases are assumed, not fitted.

## Page redesign from the Figma Make mockup (2026-11-12)
- The user made a mockup (Figma Make) from a prompt Claude wrote. I rebuilt the page in plain HTML/CSS to match its layout and style.
- The mockup's numbers were sample values, not model output (for example comps that are not in our data, a +$640 cut-rule gain, an 88% chance of leasing before the cut). They were not copied. The page shows what the model computes: the gain from the cut rule is about $20 for this house.
- The mockup banner said an outlier "is excluded from the estimate". Our model flags outliers but keeps them. The banner now describes what is really true: sources turned off by the data entry, and outliers shown as "kept".
- Sensitivity rows now match the mockup's wording (demand 20% slower, vacancy costs $25 more, and so on) but are computed by the model.
- Price grid is 1% steps, so best prices move in about $27 jumps and two scenarios can show the same price.

## Bug found by the user on the live site (2026-11-12)
- While typing in the house fields the page showed "Could not compute: check inputs" and a "high" disagreement that did not match the sources. Cause: typing sends partial values ("2", "24", "240" on the way to "2400") and an empty field is rejected by the server, and slow responses could overwrite newer ones.
- Fix: check the house fields in the page before calling the API, keep the last good result on screen with a plain message, and ignore any response that is not from the latest request.
- The AI's earlier test only typed the final value, so it missed this. The user found it by typing normally.

## Layout simplified to three zones (2026-11-13)
- The user judged the page too busy for a small landlord (many inputs, background detail on the first screen, everything one green) and sketched a layout: inputs on top, the answer and graph in the middle, "further analysis" at the bottom. He also asked for inputs in green and outputs in orange.
- The AI first rebuilt the page around the sketch: (1) house facts and the rents found, (2) the plan, three key numbers and the income chart, (3) a collapsed "Further analysis" holding the adjustment table, assumption sliders, sensitivity, house record and limits.
- Address and "available" are no longer input boxes, since they were labels only and made it look as if they changed the numbers. Model and API are unchanged; all 20 tests pass.
- Follow-up the same day: the user found the first version cramped with unreadable headings. Page widened to 1280px, text sizes raised (labels no longer tiny uppercase), explanatory lines cut, and the house list moved to a fixed left column: "My own house" first, then 18674 E 40th Pl, then any further houses.
- The user then asked to swap the colours (inputs orange, outputs green) because it looked calmer. Done; the chart is green too.
- Orange read as a warning to the user, so inputs are now blue and outputs stay green.
