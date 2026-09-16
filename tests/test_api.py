import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend", "app"))

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_network_endpoint():
    res = client.get("/api/network")
    assert res.status_code == 200
    data = res.json()
    assert len(data["nodes"]) == 16
    assert data["bridge_edge"] == ["ganhi", "akpakpa"]


def test_blockage_scenario_endpoint():
    res = client.get("/api/scenario/blockage?rounds=15&blockage_start=5&blockage_end=8")
    assert res.status_code == 200
    data = res.json()
    assert len(data["history"]["static"]["avg_time"]) == 15
    assert len(data["static_flows_by_round"]) == 15
    assert len(data["adaptive_paths_by_round"]) == 15


def test_blockage_scenario_rejects_invalid_rounds():
    res = client.get("/api/scenario/blockage?rounds=2")
    assert res.status_code == 422


if __name__ == "__main__":
    test_health()
    test_network_endpoint()
    test_blockage_scenario_endpoint()
    test_blockage_scenario_rejects_invalid_rounds()
    print("Tous les tests passent.")
