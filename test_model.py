import math
import pytest
from model import (Assumptions, Source, Subject, normalize_sources, reconcile,
                   weighted_median, evaluate, best_price, recommend,
                   plan_income, best_plan)

SUBJ = Subject(beds=3, baths=2, sqft=1700)
A = Assumptions()


def comp(id, value, **kw):
    return Source(id, id, kw.pop("type", "asking_comp"), value, beds=3, baths=2, sqft=1700,
                  age_days=0, distance_mi=0, **kw)


def test_weighted_median_hand_computed():
    # weights 1,1,2 -> total 4, half 2; running 1,2 (== half, average with next), so (20+30)/2
    assert weighted_median([10, 20, 30], [1, 1, 2]) == 25
    assert weighted_median([10, 20, 30], [1, 1, 1]) == 20


def test_single_source_gets_wide_range():
    items = normalize_sources([comp("a", 3000)], SUBJ, A)
    r = reconcile(items, A)
    assert r["estimate"] == pytest.approx(3000 * 0.97)
    assert (r["high"] - r["low"]) / r["estimate"] >= 0.15  # at least +/- 8%


def test_identical_sources_use_minimum_range():
    items = normalize_sources([comp(str(i), 3000) for i in range(4)], SUBJ, A)
    r = reconcile(items, A)
    assert r["spread_pct"] == 0
    assert r["high"] - r["estimate"] == pytest.approx(1.28 * 0.03 * r["estimate"], rel=1e-3)
    assert r["disagreement"] == "low"


def test_outlier_is_flagged_not_dropped():
    srcs = [comp("a", 3000), comp("b", 3010), comp("c", 2990), comp("d", 3005), comp("odd", 4800)]
    items = normalize_sources(srcs, SUBJ, A)
    r = reconcile(items, A)
    assert r["outliers"] == ["odd"]
    assert r["n_sources"] == 5
    assert r["estimate"] < 3100  # median barely moves


def test_more_disagreement_widens_range():
    tight = reconcile(normalize_sources([comp(str(i), v) for i, v in enumerate([2900, 3000, 3100, 3000])], SUBJ, A), A)
    loose = reconcile(normalize_sources([comp(str(i), v) for i, v in enumerate([2300, 3000, 3700, 3000])], SUBJ, A), A)
    assert (loose["high"] - loose["low"]) > (tight["high"] - tight["low"])


def test_higher_sensitivity_lowers_best_price():
    low = best_price(3000, Assumptions(price_sensitivity=4))["best"]["price"]
    high = best_price(3000, Assumptions(price_sensitivity=14))["best"]["price"]
    assert high < low


def test_evaluate_hand_computed_at_market():
    # at market x=1: p = 0.04, days = 25, months = 12 - 25/30.4
    r = evaluate(3000, 3000, A)
    months = 12 - 25 / 30.4
    expected = 3000 * months - 0.5 * 3000 - 25 * 40
    assert r["vacant_days"] == 25.0
    assert r["income_12m"] == pytest.approx(expected, abs=0.01)


def test_excluding_a_source_changes_result_and_recommend_runs():
    srcs = [comp("a", 3000), comp("b", 3400), comp("z", 2900, type="zillow_estimate")]
    full = recommend(srcs, SUBJ, A)
    srcs[0].include = False
    fewer = recommend(srcs, SUBJ, A)
    assert fewer["market"]["n_sources"] == 2
    assert full["market"]["estimate"] != fewer["market"]["estimate"]
    assert len(full["sensitivity"]) == 6 and full["recommendation"]["price"] > 0


def test_no_sources_raises():
    with pytest.raises(ValueError):
        reconcile([], A)


def test_heavily_adjusted_comp_is_capped_and_downweighted():
    tiny = Source("tiny", "tiny", "asking_comp", 2500, beds=3, baths=2, sqft=900, age_days=0, distance_mi=0)
    n = normalize_sources([tiny], SUBJ, A)[0]
    assert n.adjusted == pytest.approx(2500 * 0.97 * 1.25)   # capped at +25%
    assert n.weight == pytest.approx(0.5)                      # 1 / (1 + 4 x 0.25), vs 1.0 for a perfect comp


# ---- price plan ----

def test_plan_income_matches_hand_calc_when_lease_is_certain():
    # p = 1 means it leases on day 1: income = price*(12 - 1/30.4) - fee*price - 1*cost
    a = Assumptions(base_lease_rate=1.0)
    r = plan_income(3000, 14, 2800, 3000, a)
    expected = 3000 * (12 - 1 / 30.4) - 0.5 * 3000 - 40
    assert abs(r["income"] - expected) < 1e-6
    assert abs(r["days"] - 1) < 1e-9 and abs(r["leased_before_cut"] - 1) < 1e-9


def test_plan_without_cut_is_close_to_evaluate():
    a = Assumptions()
    r = plan_income(2716, int(a.max_vacant_days), 2716, 2716, a)
    e = evaluate(2716, 2716, a)
    assert abs(r["income"] - e["income_12m"]) < 5
    assert abs(r["days"] - e["vacant_days"]) < 0.1


def test_cut_beats_no_cut_when_start_price_is_too_high_for_the_market():
    a = Assumptions()
    cut = plan_income(3100, 14, 2750, 2750, a)["income"]
    hold = plan_income(3100, 365, 3100, 2750, a)["income"]
    assert cut > hold


def test_cut_rule_matters_more_when_sources_disagree():
    a = Assumptions()
    tight = best_plan({"estimate": 2716, "low": 2650, "high": 2780}, a)["gain"]
    wide = best_plan({"estimate": 2716, "low": 2300, "high": 3130}, a)["gain"]
    assert wide > tight >= 0


def test_best_plan_is_at_least_as_good_as_best_single_price():
    r = best_plan({"estimate": 2716, "low": 2612, "high": 2820}, Assumptions())
    assert r["plan"]["income_12m"] >= r["single"]["income_12m"] - 1e-6
    assert r["plan"]["cut_price"] < r["plan"]["start"]
