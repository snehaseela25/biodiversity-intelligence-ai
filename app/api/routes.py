import re
from typing import Dict, Any

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models.schemas import (
    ChatRequest,
    AnalyzeRequest,
    WhatIfRequest,
    EnvironmentalInput,
    AnalysisResponse,
)
from app.models.db import SessionLocal, Document
from app.memory.store import get_state, save_state, merge_state
from app.rag.retriever import retriever
from app.services.analyzer import analyze
from app.reasoning.engine import analyze_environment


router = APIRouter()


# =========================================================
# Natural language parser
# =========================================================

def parse_environmental_text(text: str) -> EnvironmentalInput:
    """
    Lightweight parser for common environmental statements.

    Example:
    "My farm is semi-arid. Soil organic carbon is 0.3%.
     Rainfall is low. I grow monoculture wheat."
    """

    lower = text.lower()

    result: Dict[str, Any] = {}

    # -----------------------------------------------------
    # Region
    # -----------------------------------------------------

    if "semi-arid" in lower or "semi arid" in lower:
        result["region"] = "semi-arid"

    # -----------------------------------------------------
    # Crop
    # -----------------------------------------------------

    crop_names = [
        "wheat",
        "rice",
        "maize",
        "corn",
        "cotton",
        "sugarcane",
        "millet",
        "soybean",
        "groundnut",
        "potato",
    ]

    for crop in crop_names:
        if crop in lower:
            result["crop"] = crop
            break

    # -----------------------------------------------------
    # Organic carbon
    # -----------------------------------------------------

    carbon_patterns = [
        r"organic carbon(?: is| of|:)?\s*(\d+(?:\.\d+)?)\s*%",
        r"organic carbon\s*(\d+(?:\.\d+)?)\s*%",
        r"carbon(?: is| of|:)?\s*(\d+(?:\.\d+)?)\s*%",
    ]

    for pattern in carbon_patterns:
        match = re.search(pattern, lower)

        if match:
            result["organic_carbon"] = float(match.group(1))
            break

    # -----------------------------------------------------
    # Soil moisture
    # -----------------------------------------------------

    moisture_patterns = [
        r"soil moisture(?: is| of|:)?\s*(\d+(?:\.\d+)?)\s*%",
        r"moisture(?: is| of|:)?\s*(\d+(?:\.\d+)?)\s*%",
    ]

    for pattern in moisture_patterns:
        match = re.search(pattern, lower)

        if match:
            result["soil_moisture"] = float(match.group(1))
            break

    # -----------------------------------------------------
    # Soil pH
    # -----------------------------------------------------

    ph_patterns = [
        r"soil ph(?: is| of|:)?\s*(\d+(?:\.\d+)?)",
        r"ph(?: is| of|:)?\s*(\d+(?:\.\d+)?)",
    ]

    for pattern in ph_patterns:
        match = re.search(pattern, lower)

        if match:
            result["soil_ph"] = float(match.group(1))
            break

    # -----------------------------------------------------
    # Temperature
    # -----------------------------------------------------

    temperature_patterns = [
        r"temperature(?: is| of|:)?\s*(\d+(?:\.\d+)?)\s*(?:°c|c)?",
        r"temp(?: is| of|:)?\s*(\d+(?:\.\d+)?)\s*(?:°c|c)?",
    ]

    for pattern in temperature_patterns:
        match = re.search(pattern, lower)

        if match:
            result["temperature"] = float(match.group(1))
            break

    # -----------------------------------------------------
    # Rainfall
    # -----------------------------------------------------

    if "very low rainfall" in lower:
        result["rainfall"] = "very low"

    elif "low rainfall" in lower:
        result["rainfall"] = "low"

    elif "declining rainfall" in lower:
        result["rainfall"] = "declining"

    elif "high rainfall" in lower:
        result["rainfall"] = "high"

    elif "heavy rainfall" in lower:
        result["rainfall"] = "heavy"

    elif "drought" in lower:
        result["rainfall"] = "drought conditions"

    # -----------------------------------------------------
    # Land use
    # -----------------------------------------------------

    if "monoculture" in lower:
        result["land_use"] = "monoculture"

    elif "intercropping" in lower:
        result["land_use"] = "intercropping"

    elif "mixed cropping" in lower:
        result["land_use"] = "mixed cropping"

    # -----------------------------------------------------
    # Pollution
    # -----------------------------------------------------

    if "high pollution" in lower:
        result["pollution"] = "high"

    elif "severe pollution" in lower:
        result["pollution"] = "severe"

    elif "pollution" in lower:
        result["pollution"] = "present"

    # -----------------------------------------------------
    # Deforestation
    # -----------------------------------------------------

    if "high deforestation" in lower:
        result["deforestation"] = "high"

    elif "severe deforestation" in lower:
        result["deforestation"] = "severe"

    elif "deforestation" in lower:
        result["deforestation"] = "present"

    # -----------------------------------------------------
    # Biodiversity status
    # -----------------------------------------------------

    if "low biodiversity" in lower:
        result["biodiversity_status"] = "low"

    elif "high biodiversity" in lower:
        result["biodiversity_status"] = "high"

    return EnvironmentalInput(**result)


# =========================================================
# Helper function
# =========================================================

def run_analysis(
    session_id: str,
    data: EnvironmentalInput,
    user_message: str = ""
):
    """Run analysis and save session memory."""

    old_state = get_state(session_id)

    new_state = data.model_dump(
        exclude_none=True
    )

    merged_state = merge_state(
        old_state,
        new_state
    )

    save_state(
        session_id,
        merged_state
    )

    merged_data = EnvironmentalInput(
        **merged_state
    )

    result = analyze(
        merged_data,
        user_message
    )

    return merged_data, result


# =========================================================
# Health
# =========================================================

@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": "Biodiversity Intelligence AI"
    }


# =========================================================
# Knowledge base
# =========================================================

@router.get("/knowledge")
def knowledge():
    db = SessionLocal()

    try:
        documents = db.query(Document).all()

        return {
            "count": len(documents),
            "documents": [
                {
                    "id": doc.id,
                    "title": doc.title,
                    "source": doc.source,
                    "year": doc.year,
                    "topic": doc.topic,
                    "url": doc.url,
                }
                for doc in documents
            ],
        }

    finally:
        db.close()


# =========================================================
# Sources
# =========================================================

@router.get("/sources")
def sources():
    db = SessionLocal()

    try:
        documents = db.query(Document).all()

        unique_sources = {}

        for doc in documents:
            unique_sources[doc.source] = doc.url

        return {
            "sources": [
                {
                    "name": source,
                    "url": url
                }
                for source, url in unique_sources.items()
            ]
        }

    finally:
        db.close()


# =========================================================
# Ingest
# =========================================================

@router.post("/ingest")
def ingest():
    try:
        filepath = (
            retriever
            .__class__
            .__module__
        )

        count = retriever.ingest_jsonl(
            settings.DOCUMENTS_DIR / "knowledge.jsonl"
        )

        return {
            "status": "success",
            "documents_added": count
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )


# =========================================================
# Analyze - natural language
# =========================================================

@router.post("/analyze")
def analyze_text(request: ChatRequest):

    parsed_data = parse_environmental_text(
        request.message
    )

    merged_data, result = run_analysis(
        request.session_id,
        parsed_data,
        request.message
    )

    return {
        "session_id": request.session_id,
        "mode": (
            "AI/RAG MODE"
            if result["llm_used"]
            else "DEMO MODE"
        ),
        "environmental_assessment": result[
            "analysis"
        ]["environmental_assessment"],
        "key_factors": result[
            "analysis"
        ]["key_factors"],
        "risk_profile": result[
            "analysis"
        ]["risk_profile"],
        "environmental_relationships": result[
            "analysis"
        ]["environmental_relationships"],
        "recommendations": result[
            "recommendations"
        ],
        "evidence": result[
            "evidence"
        ],
        "missing_information": result[
            "analysis"
        ]["missing_information"],
        "llm_used": result["llm_used"],
    }


# =========================================================
# Analyze - structured JSON
# =========================================================

@router.post("/analyze/json")
def analyze_json(request: AnalyzeRequest):

    merged_data, result = run_analysis(
        request.session_id,
        request.data,
        "Structured environmental assessment"
    )

    return {
        "session_id": request.session_id,
        "mode": (
            "AI/RAG MODE"
            if result["llm_used"]
            else "DEMO MODE"
        ),
        "environmental_assessment": result[
            "analysis"
        ]["environmental_assessment"],
        "key_factors": result[
            "analysis"
        ]["key_factors"],
        "risk_profile": result[
            "analysis"
        ]["risk_profile"],
        "environmental_relationships": result[
            "analysis"
        ]["environmental_relationships"],
        "recommendations": result[
            "recommendations"
        ],
        "evidence": result[
            "evidence"
        ],
        "missing_information": result[
            "analysis"
        ]["missing_information"],
        "llm_used": result["llm_used"],
    }


# =========================================================
# Chat
# =========================================================

@router.post("/chat")
def chat(request: ChatRequest):

    parsed_data = parse_environmental_text(
        request.message
    )

    merged_data, result = run_analysis(
        request.session_id,
        parsed_data,
        request.message
    )

    return {
        "session_id": request.session_id,
        "message": (
            result["analysis"]
            ["environmental_assessment"]
        ),
        "environmental_data": merged_data.model_dump(
            exclude_none=True
        ),
        "risk_profile": result[
            "analysis"
        ]["risk_profile"],
        "relationships": result[
            "analysis"
        ]["environmental_relationships"],
        "recommendations": result[
            "recommendations"
        ],
        "evidence": result[
            "evidence"
        ],
        "missing_information": result[
            "analysis"
        ]["missing_information"],
        "mode": (
            "AI/RAG MODE"
            if result["llm_used"]
            else "DEMO MODE"
        ),
    }


# =========================================================
# What-if analysis
# =========================================================

@router.post("/what-if")
def what_if(request: WhatIfRequest):

    if request.data:
        data = request.data

    else:
        saved = get_state(request.session_id)

        if not saved:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No environmental data found "
                    "for this session."
                )
            )

        data = EnvironmentalInput(**saved)

    scenario = request.scenario.lower()

    baseline = analyze_environment(data)

    scenario_data = data.model_copy()

    # -----------------------------------------------------
    # Rainfall decrease
    # -----------------------------------------------------

    if (
        "rainfall" in scenario
        and (
            "decrease" in scenario
            or "decrease" in scenario
            or "drop" in scenario
            or "less" in scenario
        )
    ):

        scenario_data.rainfall = "lower than baseline"

        scenario_result = analyze_environment(
            scenario_data
        )

        return {
            "scenario": request.scenario,
            "baseline": baseline,
            "scenario_result": scenario_result,
            "interpretation": (
                "Model-based inference: a decrease in rainfall "
                "would increase the water-stress context, "
                "especially where soil moisture is already low."
            ),
        }

    # -----------------------------------------------------
    # Temperature increase
    # -----------------------------------------------------

    if (
        "temperature" in scenario
        and (
            "increase" in scenario
            or "rise" in scenario
            or "higher" in scenario
        )
    ):

        if scenario_data.temperature is None:
            scenario_data.temperature = 35
        else:
            scenario_data.temperature += 2

        scenario_result = analyze_environment(
            scenario_data
        )

        return {
            "scenario": request.scenario,
            "baseline": baseline,
            "scenario_result": scenario_result,
            "interpretation": (
                "Model-based inference: higher temperature "
                "can increase evaporative demand and strengthen "
                "water-stress conditions."
            ),
        }

    return {
        "scenario": request.scenario,
        "baseline": baseline,
        "scenario_result": baseline,
        "interpretation": (
            "The current demo supports rainfall-decrease "
            "and temperature-increase scenarios."
        ),
    }