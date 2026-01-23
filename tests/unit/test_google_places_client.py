"""Unit tests for Google Maps client using mocks to avoid real API calls."""

from unittest.mock import Mock, patch

import httpx
import pytest

from compromeets.clients.google_places_client import GooglePlacesClient


class TestGooglePlacesClient:
    """Test suite for GoogleMapsClient."""

    def test_init_with_api_key(self):
        """Test client initialization with explicit API key."""
        client = GooglePlacesClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.base_url == "https://places.googleapis.com/v1/places:searchNearby"
        client.close()

    def test_init_with_env_var(self, monkeypatch):
        """Test client initialization using environment variable."""
        monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "env-key")
        client = GooglePlacesClient()
        assert client.api_key == "env-key"
        client.close()

    def test_init_missing_api_key(self, monkeypatch):
        """Test that missing API key raises ValueError."""
        monkeypatch.delenv("GOOGLE_PLACES_API_KEY", raising=False)
        with pytest.raises(ValueError, match="API key must be provided"):
            GooglePlacesClient()

    @patch("compromeets.clients.google_places_client.httpx.Client")
    def test_search_nearby_success(self, mock_client_class):
        """Test successful searching nearby request."""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [
                {
                    "displayName": "Test Place",
                    "rating": 4.5,
                    "userRatingCount": 100,
                    "location": {"latitude": 37.4224764, "longitude": -122.0842499},
                    "geometry": {"location": {"lat": 37.4224764, "lng": -122.0842499}},
                }
            ],
            "status": "OK",
        }
        mock_response.raise_for_status = Mock()

        # Setup mock client
        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Test
        client = GooglePlacesClient(api_key="test-key")
        result = client.search_nearby({"latitude": 37.4224764, "longitude": -122.0842499}, 500, ["pub"])

        # Assertions
        assert result["status"] == "OK"
        assert len(result["results"]) == 1
        mock_client.post.assert_called_once_with(
            "https://places.googleapis.com/v1/places:searchNearby",
            headers={
                "X-Goog-Api-Key": "test-key",
                "X-Goog-FieldMask": "places.displayName,places.rating,places.userRatingCount,places.location",
                "Content-Type": "application/json",
            },
            json={
                "includedTypes": ["pub"],
                "maxResultCount": 10,
                "locationRestriction": {
                    "circle": {"center": {"latitude": 37.4224764, "longitude": -122.0842499}, "radius": 500}
                },
            },
        )
        client.close()

    @patch("compromeets.clients.google_places_client.httpx.Client")
    def test_search_nearby_api_error(self, mock_client_class):
        """Test searching nearby when API returns an error."""
        # Setup mock response that raises an error
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("API Error", request=Mock(), response=Mock())

        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Test
        client = GooglePlacesClient(api_key="test-key")
        with pytest.raises(httpx.HTTPStatusError):
            client.search_nearby({"latitude": 37.4224764, "longitude": -122.0842499}, 500, ["pub"])
        client.close()

    @patch("compromeets.clients.google_places_client.httpx.Client")
    def test_search_nearby_success_with_radius(self, mock_client_class):
        """Test successful searching nearby request with radius."""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [
                {
                    "displayName": "Test Place",
                    "rating": 4.5,
                    "userRatingCount": 100,
                    "location": {"latitude": 37.4224764, "longitude": -122.0842499},
                    "geometry": {"location": {"lat": 37.4224764, "lng": -122.0842499}},
                }
            ],
            "status": "OK",
        }
        mock_response.raise_for_status = Mock()

        # Setup mock client
        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Test
        client = GooglePlacesClient(api_key="test-key")
        result = client.search_nearby({"latitude": 37.4224764, "longitude": -122.0842499}, 1000, ["pub"])

        # Assertions
        assert result["status"] == "OK"
        mock_client.post.assert_called_once_with(
            "https://places.googleapis.com/v1/places:searchNearby",
            headers={
                "X-Goog-Api-Key": "test-key",
                "X-Goog-FieldMask": "places.displayName,places.rating,places.userRatingCount,places.location",
                "Content-Type": "application/json",
            },
            json={
                "includedTypes": ["pub"],
                "maxResultCount": 10,
                "locationRestriction": {
                    "circle": {"center": {"latitude": 37.4224764, "longitude": -122.0842499}, "radius": 1000}
                },
            },
        )
        client.close()

    def test_context_manager(self):
        """Test that client can be used as a context manager."""
        with patch("compromeets.clients.google_places_client.httpx.Client") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            with GooglePlacesClient(api_key="test-key") as client:
                assert client.api_key == "test-key"

            # Verify close was called
            mock_client.close.assert_called_once()
