"""API tests: every example house must load, validate and produce a plan."""
from fastapi.testclient import TestClient

from main import app, HOUSES

client = TestClient(app)


def body_for(house_id):
    d = client.get("/api/defaults", params={"house": house_id}).json()
    p = d["property"]
    return {"subject": {"beds": p["beds"], "baths": p["baths"], "sqft": p["sqft"]}, "sources": d["sources"],
            "assumptions": d["assumptions"], "current_ask": p.get("current_asking_rent")}


def test_houses_list_includes_custom_last():
    ids = [h["id"] for h in client.get("/api/houses").json()]
    assert ids[-1] == "custom" and len(ids) >= 2


def test_unknown_house_is_404():
    assert client.get("/api/defaults", params={"house": "nope"}).status_code == 404
    assert client.get("/api/defaults", params={"house": "../main"}).status_code == 404


def test_every_example_house_gives_a_plan():
    for hid, h in HOUSES.items():
        if hid == "custom":
            continue
        assert h["sources"], hid
        assert h["property"].get("facts_source"), hid          # each house must say where its facts came from
        assert all(s.get("url") for s in h["sources"]), hid      # and each source must have a link
        r = client.post("/api/recommend", json=body_for(hid))
        assert r.status_code == 200, (hid, r.text)
        out = r.json()
        assert out["market"]["low"] < out["market"]["estimate"] < out["market"]["high"]
        assert out["plan"]["plan"]["cut_price"] < out["plan"]["plan"]["start"]


def test_custom_house_has_no_sources_and_needs_one():
    d = client.get("/api/defaults", params={"house": "custom"}).json()
    assert d["sources"] == []
    r = client.post("/api/recommend", json=body_for("custom"))
    assert r.status_code == 422


def test_custom_house_works_once_a_source_is_added():
    b = body_for("custom")
    b["sources"] = [{"id": "u1", "name": "my comp", "type": "leased_comp", "value": 2400, "beds": 3, "baths": 2, "sqft": 1500, "age_days": 10}]
    assert client.post("/api/recommend", json=b).status_code == 200


# ---- input validation (Pydantic) ----

def _valid_body():
    return body_for("e40th-18674")


def test_bad_source_type_is_rejected():
    b = _valid_body()
    b["sources"][0]["type"] = "made_up"
    assert client.post("/api/recommend", json=b).status_code == 422


def test_non_positive_rent_is_rejected():
    b = _valid_body()
    b["sources"][0]["value"] = 0
    assert client.post("/api/recommend", json=b).status_code == 422


def test_out_of_range_assumption_is_rejected():
    b = _valid_body()
    b["assumptions"]["base_lease_rate"] = 5          # a daily chance above 100%
    assert client.post("/api/recommend", json=b).status_code == 422


def test_missing_house_facts_are_rejected():
    b = _valid_body()
    del b["subject"]["sqft"]
    assert client.post("/api/recommend", json=b).status_code == 422


def test_hud_check_runs_for_default_house():
    import main
    h = main.HOUSES["e40th-18674"]
    p = h["property"]
    assert p["hud_fmr_3br"] == 2846
    body = {"subject": {"beds": p["beds"], "baths": p["baths"], "sqft": p["sqft"]},
            "sources": h["sources"], "hud_fmr": p["hud_fmr_3br"], "current_ask": 2800}
    m = client.post("/api/recommend", json=body).json()["market"]
    assert 0.8 <= m["hud_ratio"] <= 1.4
    assert "plausible band" in m["hud_note"]
