from typing import Dict, Any, List

from app.models.schemas import (
    EnvironmentalInput,
    Evidence,
    Recommendation,
)
from app.rag.retriever import retriever
from app.reasoning.engine import analyze_environment
from app.services.recommendations import generate_recommendations
from app.services.llm import generate_llm_response


def build_retrieval_query(
    data: EnvironmentalInput,
    user_message: str = ""
) -> str:
    """
    Convert environmental information into a retrieval query.
    """

    parts = []

    if user_message:
        parts.append(user_message)

    fields = {
        "region": data.region,
        "crop": data.crop,
        "soil pH": data.soil_ph,
        "organic carbon": data.organic_carbon,
        "soil moisture": data.soil_moisture,
        "land use": data.land_use,
        "species richness": data.species_richness,
        "habitat diversity": data.habitat_diversity,
        "temperature": data.temperature,
        "rainfall": data.rainfall,
        "pollution": data.pollution,
        "deforestation": data.deforestation,
        "biodiversity status": data.biodiversity_status,
    }

    for name, value in fields.items():
        if value is not None and value != "":
            parts.append(f"{name}: {value}")

    return " ".join(parts)


def convert_evidence(
    retrieved_docs: List[Dict[str, Any]]
) -> List[Evidence]:
    """Convert RAG documents into API evidence objects."""

    evidence = []

    for doc in retrieved_docs:

        evidence.append(
            Evidence(
                title=doc.get("title", "Scientific source"),
                source=doc.get("source", "Unknown"),
                year=doc.get("year"),
                topic=doc.get("topic"),
                url=doc.get("url"),
                passage=doc.get("text", ""),
                relevance=(
                    f"Retrieved scientific evidence "
                    f"(relevance score: {doc.get('score', 0)})"
                ),
            )
        )

    return evidence


def analyze(
    data: EnvironmentalInput,
    user_message: str = ""
) -> Dict[str, Any]:
    """
    Complete environmental analysis pipeline.

    Steps:
    1. Deterministic environmental reasoning
    2. RAG retrieval
    3. Recommendation generation
    4. Optional LLM synthesis
    """

    # ---------------------------------------------------------
    # Step 1: Deterministic reasoning
    # ---------------------------------------------------------

    analysis = analyze_environment(data)

    # ---------------------------------------------------------
    # Step 2: Retrieve scientific evidence
    # ---------------------------------------------------------

    retrieval_query = build_retrieval_query(
        data,
        user_message
    )

    retrieved_docs = retriever.search(
        retrieval_query,
        top_k=5
    )

    evidence = convert_evidence(retrieved_docs)

    # ---------------------------------------------------------
    # Step 3: Generate recommendations
    # ---------------------------------------------------------

    recommendations = generate_recommendations(
        data,
        retrieved_docs
    )

    # ---------------------------------------------------------
    # Step 4: Optional LLM explanation
    # ---------------------------------------------------------

    llm_result = generate_llm_response(
        user_message=user_message,
        analysis=analysis,
        evidence=retrieved_docs,
    )

    if llm_result["success"]:
        analysis["environmental_assessment"] += (
            "\n\nAI synthesis:\n"
            + llm_result["text"]
        )

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------

    return {
        "analysis": analysis,
        "recommendations": recommendations,
        "evidence": evidence,
        "llm_used": llm_result["success"],
        "llm_reason": llm_result["reason"],
    }