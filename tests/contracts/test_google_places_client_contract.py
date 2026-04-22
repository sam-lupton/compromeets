"""
Consumer-Driven Contract: PlaceSearchService (consumer) <-> GooglePlacesClient (provider)

PlaceSearchService defines what it needs from GooglePlacesClient via the GooglePlacesResponse
schema. These tests are the single source of truth for that boundary — they must pass for
any implementation of the provider, real or mocked.

Provider tests: assert that raw API response shapes validate against the schema.
Consumer tests: assert that PlaceSearchService correctly maps a valid provider response.

If either side breaks, the contract is violated and the failing test tells you which direction.
"""

from unittest.mock import Mock

import pytest
from pydantic import ValidationError
from shapely.geometry import Polygon

from compromeets.models.domain import (
    DisplayName,
    GooglePlaceRaw,
    GooglePlacesResponse,
    PlaceResult,
)
from compromeets.services.place_search_service import PlaceSearchService

# ---------------------------------------------------------------------------
# Fixture responses — representative samples of real Google Places API payloads
# ---------------------------------------------------------------------------

NEARBY_RESPONSE = {
    "places": [
        {"displayName": {"text": "The Crown"}, "rating": 4.3, "userRatingCount": 812},
        {"displayName": {"text": "The Red Lion"}, "rating": 4.1, "userRatingCount": 234},
    ]
}

TEXT_RESPONSE = {
    "places": [
        {"displayName": {"text": "Dishoom Covent Garden"}, "rating": 4.6, "userRatingCount": 9210},
    ]
}

EMPTY_RESPONSE: dict = {}  # Google returns {} when there are no results

UNRATED_RESPONSE = {
    "places": [
        {"displayName": {"text": "Brand New Spot"}},  # no rating field
    ]
}

_SEARCH_POLYGON = Polygon([(-0.1, 51.5), (-0.08, 51.5), (-0.08, 51.52), (-0.1, 51.52)])


# ---------------------------------------------------------------------------
# Provider contract: the raw API response must validate against GooglePlacesResponse
# ---------------------------------------------------------------------------


def test_provider_standard_nearby_response_validates_against_contract():
    result = GooglePlacesResponse.model_validate(NEARBY_RESPONSE)
    assert len(result.places) == 2
    assert result.places[0].displayName.text == "The Crown"
    assert result.places[0].rating == 4.3


def test_provider_text_search_response_validates_against_contract():
    result = GooglePlacesResponse.model_validate(TEXT_RESPONSE)
    assert result.places[0].displayName.text == "Dishoom Covent Garden"
    assert result.places[0].rating == 4.6


def test_provider_empty_response_validates_as_empty_places_list():
    """Google returns {} (not {"places": []}) when there are no results."""
    result = GooglePlacesResponse.model_validate(EMPTY_RESPONSE)
    assert result.places == []


def test_provider_place_without_rating_defaults_to_zero():
    result = GooglePlacesResponse.model_validate(UNRATED_RESPONSE)
    assert result.places[0].rating == 0.0


def test_provider_place_missing_display_name_violates_contract():
    """displayName is required — a provider response without it is a contract violation."""
    with pytest.raises(ValidationError):
        GooglePlacesResponse.model_validate({"places": [{"rating": 4.0}]})


# ---------------------------------------------------------------------------
# Consumer contract: PlaceSearchService correctly maps GooglePlacesResponse → list[PlaceResult]
# ---------------------------------------------------------------------------


def test_consumer_maps_provider_response_to_place_results():
    mock_client = Mock()
    mock_client.search_nearby.return_value = GooglePlacesResponse.model_validate(NEARBY_RESPONSE)
    service = PlaceSearchService(google_places_client=mock_client)

    results = service.search_nearby(search_area=_SEARCH_POLYGON, types=["pub"])

    assert all(isinstance(r, PlaceResult) for r in results)
    assert results[0].name == "The Crown"
    assert results[0].rating == 4.3


def test_consumer_returns_results_sorted_by_rating_descending():
    response = GooglePlacesResponse(
        places=[
            GooglePlaceRaw(displayName=DisplayName(text="B"), rating=3.8),
            GooglePlaceRaw(displayName=DisplayName(text="A"), rating=4.7),
        ]
    )
    mock_client = Mock()
    mock_client.search_nearby.return_value = response
    service = PlaceSearchService(google_places_client=mock_client)

    results = service.search_nearby(search_area=_SEARCH_POLYGON, types=["bar"])

    assert results[0].name == "A"
    assert results[1].name == "B"


def test_consumer_handles_empty_provider_response_gracefully():
    mock_client = Mock()
    mock_client.search_nearby.return_value = GooglePlacesResponse.model_validate(EMPTY_RESPONSE)
    service = PlaceSearchService(google_places_client=mock_client)

    results = service.search_nearby(search_area=_SEARCH_POLYGON, types=["pub"])

    assert results == []


def test_consumer_uses_text_search_for_non_google_venue_types():
    """Consumer must not pass custom types (e.g. 'rooftop bar') to the nearby endpoint."""
    mock_client = Mock()
    mock_client.search_text.return_value = GooglePlacesResponse.model_validate(TEXT_RESPONSE)
    service = PlaceSearchService(google_places_client=mock_client)

    service.search_nearby(search_area=_SEARCH_POLYGON, types=["rooftop bar"])

    mock_client.search_text.assert_called_once()
    mock_client.search_nearby.assert_not_called()
