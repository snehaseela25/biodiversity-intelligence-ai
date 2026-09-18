from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == (
        "Biodiversity Intelligence AI is running"
    )


def test_health():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"


def test_analyze_json():
    payload = {
        "session_id": "test-session",
        "data": {
            "region": "semi-arid",
            "crop": "wheat",
            "soil_ph": 7.2,
            "organic_carbon": 0.3,
            "soil_moisture": 15,
            "land_use": "monoculture",
            "species_richness": 4,
            "habitat_diversity": 2,
            "temperature": 34,
            "rainfall": "low",
            "pollution": "moderate",
            "deforestation": "moderate",
            "biodiversity_status": "low"
        }
    }

    response = client.post(
        "/analyze/json",
        json=payload
    )

    assert response.status_code == 200

    data = response.json()

    assert "environmental_assessment" in data
    assert "risk_profile" in data
    assert "recommendations" in data
    assert "evidence" in data


def test_chat():
    payload = {
        "session_id": "chat-test-session",
        "message": (
            "My farm is semi-arid. "
            "I grow wheat using monoculture. "
            "Soil organic carbon is 0.3%. "
            "Rainfall is low and soil moisture is 15%."
        )
    }

    response = client.post(
        "/chat",
        json=payload
    )

    assert response.status_code == 200

    data = response.json()

    assert "message" in data
    assert "risk_profile" in data
    assert "recommendations" in data


def test_what_if():
    payload = {
        "session_id": "what-if-test",
        "scenario": "What if rainfall decreases?",
        "data": {
            "region": "semi-arid",
            "crop": "wheat",
            "organic_carbon": 0.3,
            "soil_moisture": 15,
            "land_use": "monoculture",
            "rainfall": "low"
        }
    }

    response = client.post(
        "/what-if",
        json=payload
    )

    assert response.status_code == 200

    data = response.json()

    assert "baseline" in data
    assert "scenario_result" in data