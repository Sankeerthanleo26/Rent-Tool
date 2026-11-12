"""Rent pricing model: three plain functions, no randomness.

1. normalize_sources  - put every source on the same basis (rent this house would achieve now)
2. reconcile          - weighted median + a range that widens when sources disagree
3. best_price         - trade-off between a higher rent and more empty days

Every assumption lives in the Assumptions dataclass so it can be shown as a slider.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from typing import Optional

ASKING_TYPES = {"listing_asking", "asking_comp"}
BASE_WEIGHT = {"leased_comp": 1.5, "asking_comp": 1.0, "zillow_estimate": 0.8, "listing_asking": 0.7}


@dataclass
class Assumptions:
    asking_to_lease_discount: float = 0.03   # asking rents are cut by this share
    size_elasticity: float = 0.5             # rent change per unit of relative size difference
    per_bedroom_adj: float = 150.0           # dollars per month per bedroom difference
    per_bathroom_adj: float = 75.0           # dollars per month per bathroom difference
    base_lease_rate: float = 0.04            # daily chance of leasing when priced at market
    price_sensitivity: float = 8.0           # how fast that chance falls as price rises
    cost_per_vacant_day: float = 40.0        # carrying cost while empty (taxes, utilities, etc.)
    leasing_fee_pct: float = 0.5             # leasing fee as a share of one month's rent
    max_vacant_days: float = 365.0           # cap on expected vacant days
    min_range_pct: float = 0.03              # range never narrower than this share of the estimate
    max_adjustment_pct: float = 0.25         # comp adjustments (size, rooms) are capped at this share


@dataclass
class Subject:
    beds: float
    baths: float
    sqft: float


@dataclass
class Source:
    id: str
    name: str
    type: str                      # listing_asking | asking_comp | leased_comp | zillow_estimate
    value: float                   # monthly rent as published
    beds: Optional[float] = None
    baths: Optional[float] = None
    sqft: Optional[float] = None
    age_days: Optional[float] = None       # how old the number is
    distance_mi: Optional[float] = None    # distance from the subject (comps only)
    include: bool = True


@dataclass
class Normalized:
    id: str
    name: str
    type: str
    raw: float
    adjusted: float
    weight: float
    adjustments: list = field(default_factory=list)  # human-readable steps
    outlier: bool = False


def normalize_sources(sources: list[Source], subject: Subject, a: Assumptions) -> list[Normalized]:
    out: list[Normalized] = []
    for s in sources:
        if not s.include:
            continue
        v = s.value
        steps = []
        if s.type in ASKING_TYPES:
            v2 = v * (1 - a.asking_to_lease_discount)
            steps.append(f"asking-to-lease discount {a.asking_to_lease_discount:.0%}: {v:,.0f} -> {v2:,.0f}")
            v = v2
        if s.type == "asking_comp":
            if s.sqft and subject.sqft:
                v2 = v * (1 + a.size_elasticity * (subject.sqft / s.sqft - 1))
                steps.append(f"size {s.sqft:,.0f} vs {subject.sqft:,.0f} sqft: {v:,.0f} -> {v2:,.0f}")
                v = v2
            if s.beds is not None:
                d = (subject.beds - s.beds) * a.per_bedroom_adj
                if d:
                    steps.append(f"bedrooms {s.beds:g} vs {subject.beds:g}: {d:+,.0f}")
                    v += d
            if s.baths is not None:
                d = (subject.baths - s.baths) * a.per_bathroom_adj
                if d:
                    steps.append(f"bathrooms {s.baths:g} vs {subject.baths:g}: {d:+,.0f}")
                    v += d
        recency = 0.7 if s.age_days is None else 0.5 ** (s.age_days / 90)
        similarity = 1.0
        if s.type in ("asking_comp", "leased_comp"):
            similarity = 0.6 if s.distance_mi is None else 1 / (1 + s.distance_mi)
        if s.type == "asking_comp":
            base = s.value * (1 - a.asking_to_lease_discount)
            cap = a.max_adjustment_pct * base
            if abs(v - base) > cap:
                capped = base + math.copysign(cap, v - base)
                steps.append(f"adjustments capped at {a.max_adjustment_pct:.0%}: {v:,.0f} -> {capped:,.0f}")
                v = capped
            # the more a comp had to be adjusted, the less it is trusted
            similarity *= 1 / (1 + 4 * abs(v - base) / base)
        w = BASE_WEIGHT[s.type] * recency * similarity
        steps.append(f"weight {BASE_WEIGHT[s.type]} x recency {recency:.2f} x similarity {similarity:.2f} = {w:.2f}")
        out.append(Normalized(s.id, s.name, s.type, s.value, round(v, 2), w, steps))
    return out


def weighted_median(values: list[float], weights: list[float]) -> float:
    pairs = sorted(zip(values, weights))
    half = sum(w for _, w in pairs) / 2
    running = 0.0
    for i, (v, w) in enumerate(pairs):
        running += w
        if running > half:
            return v
        if running == half:  # exactly on the boundary: average with the next value
            return (v + pairs[i + 1][0]) / 2 if i + 1 < len(pairs) else v
    return pairs[-1][0]


def reconcile(items: list[Normalized], a: Assumptions, hud_fmr: Optional[float] = None) -> dict:
    if not items:
        raise ValueError("need at least one source")
    vals = [i.adjusted for i in items]
    wts = [i.weight for i in items]
    med = weighted_median(vals, wts)
    mad = weighted_median([abs(v - med) for v in vals], wts)
    scale = max(1.4826 * mad, a.min_range_pct * med)
    half = 1.28 * scale                       # roughly a 10th-to-90th percentile band
    if len(items) < 3:                        # too few sources to trust the spread
        half = max(half, 0.08 * med)
    for i in items:
        i.outlier = abs(i.adjusted - med) > 2.5 * scale
    spread_pct = (max(vals) - min(vals)) / med if len(vals) > 1 else 0.0
    level = "low" if spread_pct < 0.08 else "medium" if spread_pct < 0.2 else "high"
    result = {
        "estimate": round(med, 2), "low": round(med - half, 2), "high": round(med + half, 2),
        "spread_pct": round(spread_pct, 4), "disagreement": level, "n_sources": len(items),
        "outliers": [i.id for i in items if i.outlier],
    }
    if hud_fmr:
        r = med / hud_fmr
        result["hud_ratio"] = round(r, 3)
        result["hud_note"] = ("estimate is far from HUD fair market rent; check inputs"
                              if not 0.8 <= r <= 1.4 else "estimate is within a plausible band of HUD fair market rent")
    return result


def evaluate(price: float, market: float, a: Assumptions) -> dict:
    x = price / market
    p = min(1.0, a.base_lease_rate * math.exp(-a.price_sensitivity * (x - 1)))
    days = min(a.max_vacant_days, 1 / p)
    months = max(0.0, 12 - days / 30.4)
    income = price * months - a.leasing_fee_pct * price - days * a.cost_per_vacant_day
    return {"price": round(price, 2), "daily_prob": round(p, 5), "vacant_days": round(days, 1),
            "income_12m": round(income, 2)}


def best_price(market: float, a: Assumptions, lo: float = 0.85, hi: float = 1.10, step: float = 0.01) -> dict:
    n = int(round((hi - lo) / step)) + 1
    curve = [evaluate(market * (lo + k * step), market, a) for k in range(n)]
    best = max(curve, key=lambda r: r["income_12m"])
    return {"best": best, "curve": curve, "at_edge": best is curve[0] or best is curve[-1]}


def recommend(sources: list[Source], subject: Subject, a: Assumptions, hud_fmr: Optional[float] = None,
              current_ask: Optional[float] = None) -> dict:
    items = normalize_sources(sources, subject, a)
    rec = reconcile(items, a, hud_fmr)
    main = best_price(rec["estimate"], a)

    def alt(**changes):
        return best_price(rec["estimate"], Assumptions(**{**asdict(a), **changes}))["best"]["price"]

    def alt_market(m):
        return best_price(m, a)["best"]["price"]

    sensitivity = {
        "if price sensitivity is halved": alt(price_sensitivity=a.price_sensitivity * 0.5),
        "if price sensitivity is 1.5x": alt(price_sensitivity=a.price_sensitivity * 1.5),
        "if true market rent is at the low end": alt_market(rec["low"]),
        "if true market rent is at the high end": alt_market(rec["high"]),
    }
    plan = best_plan(rec, a)
    if current_ask:
        plan["ask_no_cut"] = plan_value(current_ask, int(a.max_vacant_days), current_ask, rec, a)
    return {"sources": [asdict(i) for i in items], "market": rec, "recommendation": main["best"],
            "curve": main["curve"], "at_edge": main["at_edge"], "sensitivity": sensitivity, "plan": plan}


# ---------------------------------------------------------------------------
# Price plan: "list at X; if not leased by day N, cut to Y"
# ---------------------------------------------------------------------------

CUT_DAYS = (10, 14, 21, 30, 45, 60)
CUT_SIZES = (0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.14)   # fraction taken off the starting price
SCENARIO_PROBS = (0.25, 0.50, 0.25)                      # assumed: low end / middle / high end of the market range


def lease_income(price: float, day: int, a: Assumptions) -> float:
    """12-month income if the lease starts after `day` vacant days at `price` (same formula as evaluate)."""
    months = max(0.0, 12 - day / 30.4)
    return price * months - a.leasing_fee_pct * price - day * a.cost_per_vacant_day


def plan_income(start: float, cut_day: int, cut_price: float, market: float, a: Assumptions) -> dict:
    """Expected 12-month income for ONE true market rent, simulating day by day.

    Each vacant day the house leases with probability p(price). Before the cut day the price is `start`,
    after it the price is `cut_price`. Anything still unleased at the cap is treated as leasing on the cap day.
    """
    p1 = evaluate(start, market, a)["daily_prob"]
    p2 = evaluate(cut_price, market, a)["daily_prob"]
    cap = int(a.max_vacant_days)
    alive, income, exp_days, leased_before_cut = 1.0, 0.0, 0.0, 0.0
    for day in range(1, cap + 1):
        price, p = (start, p1) if day <= cut_day else (cut_price, p2)
        if day == cap:
            p = 1.0                                   # lump the leftover probability onto the cap day
        got = alive * p
        income += got * lease_income(price, day, a)
        exp_days += got * day
        if day == cut_day:
            leased_before_cut = 1 - alive * (1 - p)
        alive *= 1 - p
    return {"income": income, "days": exp_days, "leased_before_cut": leased_before_cut}


def scenarios(market: dict) -> list[tuple[float, float]]:
    """(probability, market rent) pairs from the reconciled range: low end, middle, high end."""
    return list(zip(SCENARIO_PROBS, (market["low"], market["estimate"], market["high"])))


def plan_value(start: float, cut_day: int, cut_price: float, market: dict, a: Assumptions) -> dict:
    """Plan income averaged over the market uncertainty."""
    inc = days = before = 0.0
    for prob, m in scenarios(market):
        r = plan_income(start, cut_day, cut_price, m, a)
        inc += prob * r["income"]
        days += prob * r["days"]
        before += prob * r["leased_before_cut"]
    return {"start": round(start, 2), "cut_day": cut_day, "cut_price": round(cut_price, 2),
            "income_12m": round(inc, 2), "vacant_days": round(days, 1), "leased_before_cut": round(before, 3)}


def best_plan(market: dict, a: Assumptions, lo: float = 0.85, hi: float = 1.10, step: float = 0.01) -> dict:
    """Search start prices, cut days and cut sizes. Also finds the best single price (no cut) for comparison."""
    est = market["estimate"]
    n = int(round((hi - lo) / step)) + 1
    best = single = None
    for k in range(n):
        start = est * (lo + k * step)
        s = plan_value(start, int(a.max_vacant_days), start, market, a)  # cut day = cap means no cut
        if single is None or s["income_12m"] > single["income_12m"]:
            single = s
        for cd in CUT_DAYS:
            for c in CUT_SIZES:
                r = plan_value(start, cd, start * (1 - c), market, a)
                if best is None or r["income_12m"] > best["income_12m"]:
                    best = r
    gain = round(best["income_12m"] - single["income_12m"], 2)
    return {"plan": best, "single": single, "gain": gain}
