from typing import List, Dict, Any

from app.models.schemas import EnvironmentalInput, Recommendation, Evidence


def make_evidence(
    title: str,
    source: str,
    year: int,
    topic: str,
    url: str,
    passage: str,
) -> Evidence:
    """Create a standardized evidence object."""

    return Evidence(
        title=title,
        source=source,
        year=year,
        topic=topic,
        url=url,
        passage=passage,
        relevance="Supports the environmental management recommendation."
    )


def generate_recommendations(
    data: EnvironmentalInput,
    retrieved_docs: List[Dict[str, Any]],
) -> List[Recommendation]:
    """
    Generate transparent recommendations based on environmental
    conditions and retrieved scientific evidence.
    """

    recommendations = []

    # ---------------------------------------------------------
    # Find useful evidence from retrieved documents
    # ---------------------------------------------------------

    evidence_items = []

    for doc in retrieved_docs[:5]:
        evidence_items.append(
            make_evidence(
                title=doc.get("title", "Scientific source"),
                source=doc.get("source", "Unknown"),
                year=doc.get("year") or 2026,
                topic=doc.get("topic") or "environment",
                url=doc.get("url"),
                passage=doc.get("text", ""),
            )
        )

    # ---------------------------------------------------------
    # Recommendation 1: Crop diversification
    # ---------------------------------------------------------

    land_use = str(data.land_use or "").lower()

    if (
        "monoculture" in land_use
        or "single crop" in land_use
        or (
            data.habitat_diversity is not None
            and data.habitat_diversity < 6
        )
    ):

        recommendations.append(
            Recommendation(
                action=(
                    "Increase crop and habitat diversity through "
                    "crop rotation, intercropping, field margins, "
                    "or other locally suitable diversification practices."
                ),
                why=(
                    "The supplied information indicates a relatively "
                    "simplified production or habitat system. Diversification "
                    "can support soil biological processes and provide a wider "
                    "range of habitat conditions."
                ),
                impacted_metrics=[
                    "Biodiversity",
                    "Habitat condition",
                    "Soil health",
                    "Ecosystem resilience",
                ],
                timeframe="Seasonal to multi-year",
                evidence_strength="Moderate",
                feasibility="Moderate",
                confidence=0.82,
                evidence=evidence_items[:3],
            )
        )

    # ---------------------------------------------------------
    # Recommendation 2: Soil carbon and soil cover
    # ---------------------------------------------------------

    if (
        data.organic_carbon is not None
        and data.organic_carbon < 0.5
    ) or (
        data.soil_moisture is not None
        and data.soil_moisture < 20
    ):

        recommendations.append(
            Recommendation(
                action=(
                    "Increase soil cover and organic inputs using locally "
                    "appropriate practices such as residue retention, "
                    "cover crops, compost or other organic amendments."
                ),
                why=(
                    "Low soil organic carbon and/or low soil moisture "
                    "indicates a need to improve soil condition and "
                    "water-related functions. The appropriate practice "
                    "depends on local soil, crop and climate conditions."
                ),
                impacted_metrics=[
                    "Soil health",
                    "Soil organic carbon",
                    "Water availability",
                    "Soil biological activity",
                ],
                timeframe="Several seasons to multiple years",
                evidence_strength="Moderate",
                feasibility="Moderate",
                confidence=0.86,
                evidence=evidence_items[:3],
            )
        )

    # ---------------------------------------------------------
    # Recommendation 3: Habitat restoration/protection
    # ---------------------------------------------------------

    rainfall_text = str(data.rainfall or "").lower()

    if (
        "low" in rainfall_text
        or "dry" in rainfall_text
        or "drought" in rainfall_text
        or "semi-arid" in rainfall_text
        or (
            data.habitat_diversity is not None
            and data.habitat_diversity < 3
        )
    ):

        recommendations.append(
            Recommendation(
                action=(
                    "Protect existing natural habitat and restore suitable "
                    "local vegetation where feasible, prioritizing native "
                    "species and ecological connectivity."
                ),
                why=(
                    "Low rainfall or limited habitat diversity can increase "
                    "the importance of protecting remaining suitable habitat "
                    "and reducing additional ecological stress."
                ),
                impacted_metrics=[
                    "Habitat condition",
                    "Biodiversity",
                    "Ecological connectivity",
                    "Ecosystem resilience",
                ],
                timeframe="Multi-year",
                evidence_strength="Moderate",
                feasibility="Site dependent",
                confidence=0.79,
                evidence=evidence_items[:3],
            )
        )

    # ---------------------------------------------------------
    # Recommendation 4: Pollution management
    # ---------------------------------------------------------

    pollution_text = str(data.pollution or "").lower()

    if any(
        word in pollution_text
        for word in ["high", "severe", "heavy", "significant"]
    ):

        recommendations.append(
            Recommendation(
                action=(
                    "Identify the major pollution source, reduce exposure "
                    "where feasible, and establish periodic environmental "
                    "monitoring."
                ),
                why=(
                    "Pollution can place additional pressure on biodiversity "
                    "and ecosystem functions. Management should be based on "
                    "the pollutant, source, concentration and exposure pathway."
                ),
                impacted_metrics=[
                    "Biodiversity",
                    "Water quality",
                    "Soil health",
                    "Ecosystem health",
                ],
                timeframe="Immediate monitoring; medium-term management",
                evidence_strength="Strong",
                feasibility="Depends on source",
                confidence=0.84,
                evidence=evidence_items[:3],
            )
        )

    # ---------------------------------------------------------
    # Recommendation 5: Baseline monitoring
    # ---------------------------------------------------------

    if not recommendations:

        recommendations.append(
            Recommendation(
                action=(
                    "Establish a baseline environmental monitoring program "
                    "covering soil, water, vegetation and biodiversity indicators."
                ),
                why=(
                    "A baseline makes it possible to detect environmental "
                    "change over time and identify emerging risks before "
                    "making highly specific management decisions."
                ),
                impacted_metrics=[
                    "Soil health",
                    "Water availability",
                    "Habitat condition",
                    "Biodiversity",
                ],
                timeframe="Start now; repeat periodically",
                evidence_strength="Moderate",
                feasibility="High",
                confidence=0.76,
                evidence=evidence_items[:3],
            )
        )

    return recommendations