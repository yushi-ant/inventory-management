"""
Tests for restock API endpoints.
"""
from datetime import datetime

import pytest

import mock_data
from main import DEFAULT_LEAD_TIME_DAYS


@pytest.fixture(autouse=True)
def isolate_restock_state():
    """Snapshot and restore restock_orders (memory + disk) so POST tests don't leak."""
    snapshot = list(mock_data.restock_orders)
    yield
    mock_data.restock_orders[:] = snapshot
    mock_data.save_json_file('restock_orders.json', snapshot)


class TestRestockRecommendationsEndpoint:
    """Test suite for GET /api/restock/recommendations."""

    def test_get_recommendations_within_budget(self, client):
        """Test that recommendations stay within the requested budget."""
        budget = 25000
        response = client.get(f"/api/restock/recommendations?budget={budget}")
        assert response.status_code == 200

        data = response.json()
        assert data["budget"] == budget
        assert data["total_cost"] <= budget
        assert abs((data["total_cost"] + data["remaining_budget"]) - budget) < 0.01
        assert data["lead_time_days"] == DEFAULT_LEAD_TIME_DAYS
        assert isinstance(data["items"], list)

    def test_recommendation_item_structure(self, client):
        """Test that recommended line items have the proper structure."""
        response = client.get("/api/restock/recommendations?budget=50000")
        assert response.status_code == 200

        data = response.json()
        assert len(data["items"]) > 0

        for item in data["items"]:
            assert "sku" in item
            assert "name" in item
            assert isinstance(item["quantity"], int)
            assert item["quantity"] >= 1
            assert isinstance(item["unit_cost"], (int, float))
            assert isinstance(item["line_total"], (int, float))
            assert abs(item["line_total"] - item["quantity"] * item["unit_cost"]) < 0.01

    def test_recommendation_rationale_fields(self, client):
        """Test that each recommended item exposes the rationale behind it."""
        response = client.get("/api/restock/recommendations?budget=50000")
        assert response.status_code == 200

        data = response.json()
        assert len(data["items"]) > 0

        for item in data["items"]:
            assert isinstance(item["quantity_on_hand"], int)
            assert isinstance(item["forecasted_demand"], int)
            assert item["shortfall"] == item["forecasted_demand"] - item["quantity_on_hand"]
            assert item["trend"] in ("increasing", "stable", "decreasing")
            assert isinstance(item["priority_score"], (int, float))
            # Recommended quantity never exceeds the shortfall
            assert item["quantity"] <= item["shortfall"]

    def test_get_recommendations_zero_budget(self, client):
        """Test that a zero budget yields no items."""
        response = client.get("/api/restock/recommendations?budget=0")
        assert response.status_code == 200

        data = response.json()
        assert data["items"] == []
        assert data["total_cost"] == 0
        assert data["remaining_budget"] == 0

    def test_get_recommendations_missing_budget(self, client):
        """Test that omitting the budget query param returns a validation error."""
        response = client.get("/api/restock/recommendations")
        assert response.status_code == 422


class TestRestockOrdersEndpoint:
    """Test suite for POST/GET /api/restock/orders."""

    def _payload(self):
        return {
            "budget": 25000,
            "items": [
                {
                    "sku": "PCB-001",
                    "name": "Single Layer PCB Assembly",
                    "quantity": 10,
                    "unit_cost": 24.99,
                    "line_total": 249.90,
                }
            ],
        }

    def test_create_restock_order(self, client):
        """Test creating a restock order returns 201 with computed fields."""
        response = client.post("/api/restock/orders", json=self._payload())
        assert response.status_code == 201

        order = response.json()
        assert order["order_number"].startswith("RST-")
        assert order["status"] == "Ordered"
        assert order["lead_time_days"] == DEFAULT_LEAD_TIME_DAYS
        assert abs(order["total_cost"] - 249.90) < 0.01

        submitted = datetime.fromisoformat(order["submitted_at"])
        expected = datetime.fromisoformat(order["expected_delivery"])
        assert (expected - submitted).days == DEFAULT_LEAD_TIME_DAYS

    def test_create_restock_order_empty_items(self, client):
        """Test that an empty items list is rejected with 400."""
        response = client.post("/api/restock/orders", json={"budget": 1000, "items": []})
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data

    def test_list_restock_orders_contains_created(self, client):
        """Test that GET /api/restock/orders returns a just-created order."""
        created = client.post("/api/restock/orders", json=self._payload()).json()

        response = client.get("/api/restock/orders")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        ids = [o["id"] for o in data]
        assert created["id"] in ids

    def test_create_restock_order_persists_to_disk(self, client):
        """Test that creating an order writes through to restock_orders.json."""
        created = client.post("/api/restock/orders", json=self._payload()).json()

        on_disk = mock_data.load_json_file('restock_orders.json')
        ids = [o["id"] for o in on_disk]
        assert created["id"] in ids
