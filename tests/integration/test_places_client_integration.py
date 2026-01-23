"""
Integration tests for Google Places client.

These tests make real API calls and should only be run manually or in CI with proper API keys.
Use pytest markers to skip these by default:

    pytest -m "not integration"  # Skip integration tests
    pytest -m integration        # Run only integration tests
"""

import os

import pytest

from compromeets.clients.google_places_client import GooglePlacesClient


@pytest.mark.integration
class TestGooglePlacesClientIntegration:
    """Integration tests that make real API calls."""

    @pytest.fixture
    def client(self):
        """Create a client instance for integration testing."""
        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not api_key:
            pytest.skip("GOOGLE_PLACES_API_KEY not set, skipping integration tests")
        client = GooglePlacesClient(api_key=api_key)
        yield client
        client.close()

    def test_search_nearby_real_api(self, client):
        """Test searching nearby with real API (requires valid API key)."""
        result = client.search_nearby({"latitude": 37.7937, "longitude": -122.3965}, 500, ["pub"])
        assert result["code"] == "OK"
        assert len(result["places"]) > 0
        assert "displayName" in result["places"][0]
        assert "rating" in result["places"][0]
        assert "userRatingCount" in result["places"][0]
        assert "location" in result["places"][0]

    def test_search_nearby_real_api_with_radius(self, client):
        """Test searching nearby with real API and radius (requires valid API key)."""
        result = client.search_nearby({"latitude": 37.7937, "longitude": -122.3965}, 1000, ["pub"])
        assert result["code"] == "OK"
        assert len(result["places"]) > 0
        assert "displayName" in result["places"][0]
        assert "rating" in result["places"][0]
        assert "userRatingCount" in result["places"][0]
        assert "location" in result["places"][0]
