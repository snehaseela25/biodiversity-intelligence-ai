from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


class EnvironmentalInput(BaseModel):
    region: Optional[str] = None
    crop: Optional[str] = None

    soil_ph: Optional[float] = Field(default=None, description="Soil pH")
    organic_carbon: Optional[float] = Field(
        default=None,
        description="Soil organic carbon percentage"
    )
    soil_moisture: Optional[float] = Field(
        default=None,
        description="Soil moisture percentage"
    )

    land_use: Optional[str] = None

    species_richness: Optional[float] = None
    habitat_diversity: Optional[float] = None

    temperature: Optional[float] = None
    rainfall: Optional[str] = None

    pollution: Optional[str] = None
    deforestation: Optional[str] = None

    biodiversity_status: Optional[str] = None

    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ChatRequest(BaseModel):
    session_id: str = "default"
    message: str


class AnalyzeRequest(BaseModel):
    session_id: str = "default"
    data: EnvironmentalInput


class WhatIfRequest(BaseModel):
    session_id: str = "default"
    scenario: str
    data: Optional[EnvironmentalInput] = None


class Evidence(BaseModel):
    title: str
    source: str
    year: Optional[int] = None
    topic: Optional[str] = None
    url: Optional[str] = None
    passage: str
    relevance: str = "Relevant scientific evidence"


class Recommendation(BaseModel):
    action: str
    why: str
    impacted_metrics: List[str]
    timeframe: str
    evidence_strength: str
    feasibility: str
    confidence: float
    evidence: List[Evidence] = []


class AnalysisResponse(BaseModel):
    session_id: str
    mode: str

    environmental_assessment: str
    key_factors: List[str]

    risk_profile: Dict[str, Any]

    environmental_relationships: List[str]

    recommendations: List[Recommendation]

    evidence: List[Evidence]

    missing_information: List[str] = []

    what_if: Optional[Dict[str, Any]] = None

    llm_used: bool = False