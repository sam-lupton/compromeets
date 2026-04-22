"""Unit tests for GooglePlacesClient."""

from unittest.mock import Mock, patch

import httpx
import pytest

from compromeets.clients.google_places_client import GooglePlacesClient
from compromeets.models.domain import GooglePlacesResponse, PlaceSearchLocationData

_LOCATION = PlaceSearchLocationData(latitude=51.5, longitude=-0.1, radius=500)

_VALID_API_RESPONSE = {
    "places": [
        {"displayName": {"text": "The Crown"}, "rating": 4.3, "userRatingCount": 120},
    ]
}


class TestGooglePlacesClient:
    def test_init_with_explicit_api_key(self):
        client = GooglePlacesClient(api_key="test-key")
        assert client.api_key == "test-key"
        client.close()

    def test_init_falls_back_to_env_var(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "env-key")
        client = GooglePlacesClient()
        assert client.api_key == "env-key"
        client.close()

    def test_init_raises_when_no_api_key(self, monkeypatch):
        monkeypatch.delenv("GOOGLE_PLACES_API_KEY", raising=False)
        with pytest.raises(ValueError, match="API key must be provided"):
            GooglePlacesClient()

    @patch("compromeets.clients.google_places_client.httpx.Client")
    def test_given_valid_response_when_searching_nearby_then_returns_google_places_response(self, mock_client_class):
        # Given
        mock_response = Mock()
        mock_response.json.return_value = _VALID_API_RESPONSE
        mock_response.raise_for_status = Mock()
        mock_client_class.return_value = Mock(post=Mock(return_value=mock_response))

        # When
        client = GooglePlacesClient(api_key="test-key")
        result = client.search_nearby(location_data=_LOCATION, types=["pub"])
        client.close()

        # Then
        assert isinstance(result, GooglePlacesResponse)
        assert result.places[0].displayName.text == "The Crown"
        assert result.places[0].rating == 4.3

    @patch("compromeets.clients.google_places_client.httpx.Client")
    def test_given_api_error_when_searching_nearby_then_raises_value_error(self, mock_client_class):
        # Given
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Invalid request"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "API Error", request=Mock(), response=mock_response
        )
        mock_client_class.return_value = Mock(post=Mock(return_value=mock_response))

        # When / Then
        client = GooglePlacesClient(api_key="test-key")
        with pytest.raises(ValueError, match="Google Places API error"):
            client.search_nearby(location_data=_LOCATION, types=["pub"])
        client.close()

    def test_context_manager_closes_http_client_on_exit(self):
        with patch("compromeets.clients.google_places_client.httpx.Client") as mock_client_class:
            mock_http = Mock()
            mock_client_class.return_value = mock_http

            with GooglePlacesClient(api_key="test-key"):
                pass

            mock_http.close.assert_called_once()
