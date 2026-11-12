import math
import pytest
from model import (Assumptions, Source, Subject, normalize_sources, reconcile,
                   weighted_median, evaluate, best_price, recommend)

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
    assert set(full["sensitivity"]) and full["recommendation"]["price"] > 0


def test_no_sources_raises():
    with pytest.raises(ValueError):
        reconcile([], A)


def test_heavily_adjusted_comp_is_capped_and_downweighted():
    tiny = Source("tiny", "tiny", "asking_comp", 2500, beds=3, baths=2, sqft=900, age_days=0, distance_mi=0)
    n = normalize_sources([tiny], SUBJ, A)[0]
    assert n.adjusted == pytest.approx(2500 * 0.97 * 1.25)   # capped at +25%
    assert n.weight == pytest.approx(0.5)                      # 1 / (1 + 4 x 0.25), vs 1.0 for a perfect comp
