from typing import Dict, List, Any

from app.models.schemas import EnvironmentalInput


# ---------------------------------------------------------
# Missing information required for a detailed assessment
# ---------------------------------------------------------

MISSING_MAP = {
    "soil_ph": "soil pH",
    "organic_carbon": "soil organic carbon percentage",
    "soil_moisture": "soil moisture percentage",
    "rainfall": "rainfall pattern",
    "land_use": "land-use type",
    "region": "region or location",
}


def find_missing_information(data: EnvironmentalInput) -> List[str]:
    """Find important environmental variables that are not supplied."""

    missing = []

    for field, label in MISSING_MAP.items():
        value = getattr(data, field, None)

        if value is None or value == "":
            missing.append(label)

    return missing


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def normalize_text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip().lower()


def is_low_rainfall(value: Any) -> bool:
    text = normalize_text(value)

    return any(
        word in text
        for word in [
            "low",
            "very low",
            "poor",
            "declining",
            "drought",
            "dry",
            "semi-arid",
        ]
    )


def is_high_rainfall(value: Any) -> bool:
    text = normalize_text(value)

    return any(
        word in text
        for word in [
            "high",
            "very high",
            "heavy",
            "excess",
            "flood",
        ]
    )


def is_monoculture(value: Any) -> bool:
    text = normalize_text(value)

    return any(
        word in text
        for word in [
            "monoculture",
            "single crop",
            "single-crop",
        ]
    )


def is_low_habitat(value: Any) -> bool:
    text = normalize_text(value)

    return any(
        word in text
        for word in [
            "low",
            "limited",
            "poor",
            "fragmented",
        ]
    )


def is_high_pollution(value: Any) -> bool:
    text = normalize_text(value)

    return any(
        word in text
        for word in [
            "high",
            "severe",
            "heavy",
            "significant",
        ]
    )


def is_high_deforestation(value: Any) -> bool:
    text = normalize_text(value)

    return any(
        word in text
        for word in [
            "high",
            "severe",
            "heavy",
            "rapid",
        ]
    )


# ---------------------------------------------------------
# Risk scoring
# ---------------------------------------------------------

def calculate_risk_profile(
    data: EnvironmentalInput
) -> Dict[str, Any]:
    """
    Transparent demonstration risk rules.

    These scores are not field-calibrated ecological indices.
    They are intended to explain relationships in a demo.
    """

    soil_score = 0
    water_score = 0
    habitat_score = 0
    biodiversity_score = 0
    human_score = 0

    reasons = []

    # Soil organic carbon
    if data.organic_carbon is not None:
        if data.organic_carbon < 0.5:
            soil_score += 2
            reasons.append(
                "Low soil organic carbon is treated as a soil-function concern."
            )
        elif data.organic_carbon < 1.0:
            soil_score += 1

    # Soil pH
    if data.soil_ph is not None:
        if data.soil_ph < 5 or data.soil_ph > 8.5:
            soil_score += 2
            reasons.append(
                "Very acidic or alkaline soil pH may constrain some soil processes."
            )
        elif data.soil_ph < 5.5 or data.soil_ph > 8:
            soil_score += 1

    # Soil moisture
    if data.soil_moisture is not None:
        if data.soil_moisture < 20:
            water_score += 2
            reasons.append(
                "Low soil moisture is treated as a water-availability concern."
            )
        elif data.soil_moisture < 35:
            water_score += 1

    # Rainfall
    if is_low_rainfall(data.rainfall):
        water_score += 2
        reasons.append(
            "Low or declining rainfall increases water-stress context."
        )

    if is_high_rainfall(data.rainfall):
        water_score += 1

    # Temperature
    if data.temperature is not None:
        if data.temperature >= 35:
            water_score += 1
            reasons.append(
                "High temperature can increase evaporative demand and water stress."
            )

    # Land use
    if is_monoculture(data.land_use):
        habitat_score += 2
        biodiversity_score += 2
        reasons.append(
            "Monoculture is treated as lower habitat diversity than a diversified system."
        )

    # Habitat diversity
    if data.habitat_diversity is not None:
        if data.habitat_diversity < 3:
            habitat_score += 2
            biodiversity_score += 2
        elif data.habitat_diversity < 6:
            habitat_score += 1
            biodiversity_score += 1

    # Species richness
    if data.species_richness is not None:
        if data.species_richness < 5:
            biodiversity_score += 2
        elif data.species_richness < 10:
            biodiversity_score += 1

    # Pollution
    if is_high_pollution(data.pollution):
        human_score += 2
        biodiversity_score += 1
        reasons.append(
            "Higher pollution exposure can place additional pressure on ecosystems."
        )

    # Deforestation
    if is_high_deforestation(data.deforestation):
        human_score += 2
        habitat_score += 2
        biodiversity_score += 2
        reasons.append(
            "Deforestation or habitat disturbance can reduce habitat availability."
        )

    # Keep scores within a simple 0-5 scale
    scores = {
        "soil_health": min(soil_score, 5),
        "water_availability": min(water_score, 5),
        "habitat_condition": min(habitat_score, 5),
        "biodiversity": min(biodiversity_score, 5),
        "human_impact": min(human_score, 5),
    }

    # Convert scores to labels
    labels = {}

    for metric, score in scores.items():

        if score >= 4:
            label = "HIGH CONCERN"
        elif score >= 2:
            label = "MODERATE CONCERN"
        else:
            label = "LOW CONCERN"

        labels[metric] = {
            "score": score,
            "label": label,
        }

    return {
        "metrics": labels,
        "explanation": reasons,
        "scale": "0-5 demonstration score; higher means greater concern",
    }


# ---------------------------------------------------------
# Environmental relationships
# ---------------------------------------------------------

def identify_relationships(
    data: EnvironmentalInput
) -> List[str]:

    relationships = []

    if (
        data.organic_carbon is not None
        and data.organic_carbon < 0.5
        and data.soil_moisture is not None
        and data.soil_moisture < 20
    ):
        relationships.append(
            "Low soil organic carbon and low soil moisture together indicate "
            "a linked soil-function and water-stress concern."
        )

    if (
        is_low_rainfall(data.rainfall)
        and data.soil_moisture is not None
        and data.soil_moisture < 20
    ):
        relationships.append(
            "Low rainfall and low soil moisture reinforce the possibility "
            "of water stress."
        )

    if (
        is_monoculture(data.land_use)
        and (
            data.habitat_diversity is None
            or data.habitat_diversity < 6
        )
    ):
        relationships.append(
            "Monoculture combined with limited habitat diversity may reduce "
            "the range of habitats available to organisms."
        )

    if (
        data.temperature is not None
        and data.temperature >= 35
        and is_low_rainfall(data.rainfall)
    ):
        relationships.append(
            "High temperature together with low rainfall creates a stronger "
            "climatic water-stress context."
        )

    if is_high_pollution(data.pollution):
        relationships.append(
            "Pollution adds an additional pressure that can interact with "
            "existing habitat and biodiversity stresses."
        )

    if is_high_deforestation(data.deforestation):
        relationships.append(
            "Habitat disturbance can interact with biodiversity loss by "
            "reducing or fragmenting suitable habitat."
        )

    return relationships


# ---------------------------------------------------------
# Main analysis function
# ---------------------------------------------------------

def analyze_environment(
    data: EnvironmentalInput
) -> Dict[str, Any]:

    missing = find_missing_information(data)

    risk_profile = calculate_risk_profile(data)

    relationships = identify_relationships(data)

    key_factors = []

    if data.organic_carbon is not None:
        key_factors.append(
            f"Soil organic carbon: {data.organic_carbon}%"
        )

    if data.soil_ph is not None:
        key_factors.append(
            f"Soil pH: {data.soil_ph}"
        )

    if data.soil_moisture is not None:
        key_factors.append(
            f"Soil moisture: {data.soil_moisture}%"
        )

    if data.rainfall:
        key_factors.append(
            f"Rainfall: {data.rainfall}"
        )

    if data.land_use:
        key_factors.append(
            f"Land use: {data.land_use}"
        )

    if data.crop:
        key_factors.append(
            f"Crop: {data.crop}"
        )

    if data.temperature is not None:
        key_factors.append(
            f"Temperature: {data.temperature}°C"
        )

    if data.pollution:
        key_factors.append(
            f"Pollution: {data.pollution}"
        )

    if data.deforestation:
        key_factors.append(
            f"Deforestation/habitat disturbance: {data.deforestation}"
        )

    metrics = risk_profile["metrics"]

    concern_count = sum(
        1
        for item in metrics.values()
        if item["score"] >= 2
    )

    if concern_count >= 3:
        overall = (
            "The supplied environmental conditions show multiple "
            "areas of ecological concern that should be monitored "
            "and addressed through context-specific management."
        )

    elif concern_count >= 1:
        overall = (
            "The supplied environmental conditions show some "
            "areas that may require monitoring and targeted management."
        )

    else:
        overall = (
            "The supplied environmental conditions do not trigger "
            "the demonstration concern rules. Continued monitoring "
            "is still recommended."
        )

    return {
        "environmental_assessment": overall,
        "key_factors": key_factors,
        "risk_profile": risk_profile,
        "environmental_relationships": relationships,
        "missing_information": missing,
    }