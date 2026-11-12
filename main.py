"""FastAPI app: serves the page and one endpoint that runs the model."""
import json
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from model import Assumptions, Source, Subject, recommend

ROOT = Path(__file__).parent
app = FastAPI(title="Rent pricing tool")


class SourceIn(BaseModel):
    id: str
    name: str
    type: str = Field(pattern="^(listing_asking|asking_comp|leased_comp|zillow_estimate)$")
    value: float = Field(gt=0)
    beds: Optional[float] = None
    baths: Optional[float] = None
    sqft: Optional[float] = Field(default=None, gt=0)
    age_days: Optional[float] = Field(default=None, ge=0)
    distance_mi: Optional[float] = Field(default=None, ge=0)
    include: bool = True


class SubjectIn(BaseModel):
    beds: float = Field(ge=0)
    baths: float = Field(ge=0)
    sqft: float = Field(gt=0)


class AssumptionsIn(BaseModel):
    asking_to_lease_discount: float = Field(0.03, ge=0, le=0.3)
    size_elasticity: float = Field(0.5, ge=0, le=1.5)
    per_bedroom_adj: float = Field(150, ge=0, le=1000)
    per_bathroom_adj: float = Field(75, ge=0, le=1000)
    base_lease_rate: float = Field(0.04, gt=0, le=1)
    price_sensitivity: float = Field(8, ge=0, le=40)
    cost_per_vacant_day: float = Field(40, ge=0, le=500)
    leasing_fee_pct: float = Field(0.5, ge=0, le=2)
    max_vacant_days: float = Field(365, gt=0, le=730)
    min_range_pct: float = Field(0.03, ge=0, le=0.3)
    max_adjustment_pct: float = Field(0.25, ge=0, le=1)


class RecommendIn(BaseModel):
    subject: SubjectIn
    sources: list[SourceIn]
    assumptions: AssumptionsIn = AssumptionsIn()
    hud_fmr: Optional[float] = Field(default=None, gt=0)
    current_ask: Optional[float] = Field(default=None, gt=0)


@app.get("/api/defaults")
def defaults():
    prop = json.loads((ROOT / "data/property.json").read_text())
    src = json.loads((ROOT / "data/sources.json").read_text())
    return {"property": prop, "sources": src["sources"], "sources_status": src["status"],
            "assumptions": asdict(Assumptions())}


@app.post("/api/recommend")
def api_recommend(body: RecommendIn):
    sources = [Source(**s.model_dump()) for s in body.sources]
    if not any(s.include for s in sources):
        raise HTTPException(422, "Turn on at least one source.")
    return recommend(sources, Subject(**body.subject.model_dump()),
                     Assumptions(**body.assumptions.model_dump()), body.hud_fmr, body.current_ask)


@app.get("/")
def index():
    return FileResponse(ROOT / "static/index.html")


app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
