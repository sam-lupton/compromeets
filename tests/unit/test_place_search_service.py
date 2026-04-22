"""
Unit tests for PlaceSearchService — structured with Given / When / Then.

Naming convention: test_given_<context>_when_<action>_then_<outcome>
"""

from unittest.mock import Mock

import pytest
from shapely.geometry import Polygon

from compromeets.models.domain import (
    DisplayName,
    GooglePlaceRaw,
    GooglePlacesResponse,
    PlaceResult,
    PlaceSearchLocationData,
)
from compromeets.services.place_search_service import PlaceSearchService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_service() -> PlaceSearchService:
    return PlaceSearchService(google_places_client=Mock())


def _square_polygon() -> Polygon:
    return Polygon([(-0.1, 51.5), (-0.08, 51.5), (-0.08, 51.52), (-0.1, 51.52)])


def _places_response(*pairs: tuple[str, float]) -> GooglePlacesResponse:
    return GooglePlacesResponse(
        places=[GooglePlaceRaw(displayName=DisplayName(text=name), rating=rating) for name, rating in pairs]
    )


# ---------------------------------------------------------------------------
# overlap_to_location_data
# ---------------------------------------------------------------------------

def test_given_a_square_polygon_when_converting_to_location_data_then_returns_centroid_and_positive_radius():
    # Given
    service = _make_service()
    polygon = _square_polygon()

    # When
    location_data = service.overlap_to_location_data(polygon)

    # Then
    assert isinstance(location_data, PlaceSearchLocationData)
    assert location_data.latitude == pytest.approx(51.51, abs=0.01)
    assert location_data.longitude == pytest.approx(-0.09, abs=0.01)
    assert location_data.radius > 0
    assert isinstance(location_data.radius, int)


# ---------------------------------------------------------------------------
# sort_places
# ---------------------------------------------------------------------------

def test_given_multiple_places_when_sorting_then_returns_highest_rated_first():
    # Given
    service = _make_service()
    results = _places_response(("Place A", 3.5), ("Place B", 4.5), ("Place C", 4.0))

    # When
    sorted_places = service.sort_places(results)

    # Then
    assert len(sorted_places) == 3
    assert sorted_places[0] == PlaceResult(name="Place B", rating=4.5)
    assert sorted_places[1] == PlaceResult(name="Place C", rating=4.0)
    assert sorted_places[2] == PlaceResult(name="Place A", rating=3.5)


def test_given_a_place_with_no_rating_when_sorting_then_defaults_rating_to_zero():
    # Given
    service = _make_service()
    results = GooglePlacesResponse(
        places=[
            GooglePlaceRaw(displayName=DisplayName(text="Place A"), rating=4.0),
            GooglePlaceRaw(displayName=DisplayName(text="Place B")),  # rating defaults to 0.0
            GooglePlaceRaw(displayName=DisplayName(text="Place C"), rating=5.0),
        ]
    )

    # When
    sorted_places = service.sort_places(results)

    # Then
    assert sorted_places[0] == PlaceResult(name="Place C", rating=5.0)
    assert sorted_places[1] == PlaceResult(name="Place A", rating=4.0)
    assert sorted_places[2] == PlaceResult(name="Place B", rating=0.0)


# ---------------------------------------------------------------------------
# search_nearby
# ---------------------------------------------------------------------------

def test_given_valid_google_types_when_searching_nearby_then_calls_client_and_returns_sorted_place_results():
    # Given
    mock_client = Mock()
    mock_client.search_nearby.return_value = _places_response(("Pub A", 4.0), ("Pub B", 4.5))
    service = PlaceSearchService(google_places_client=mock_client)
    polygon = _square_polygon()

    # When
    results = service.search_nearby(search_area=polygon, types=["pub"])

    # Then
    assert len(results) == 2
    assert all(isinstance(r, PlaceResult) for r in results)
    assert results[0] == PlaceResult(name="Pub B", rating=4.5)
    assert results[1] == PlaceResult(name="Pub A", rating=4.0)

    mock_client.search_nearby.assert_called_once()
    call_args = mock_client.search_nearby.call_args
    assert isinstance(call_args.kwargs["location_data"], PlaceSearchLocationData)
    assert call_args.kwargs["types"] == ["pub"]


def test_given_a_custom_venue_type_when_searching_nearby_then_falls_back_to_text_search():
    # Given
    mock_client = Mock()
    mock_client.search_text.return_value = _places_response(("Rooftop Bar", 4.7))
    service = PlaceSearchService(google_places_client=mock_client)
    polygon = _square_polygon()

    # When
    results = service.search_nearby(search_area=polygon, types=["rooftop bar"])

    # Then
    assert results == [PlaceResult(name="Rooftop Bar", rating=4.7)]
    mock_client.search_text.assert_called_once()
    mock_client.search_nearby.assert_not_called()


# ---------------------------------------------------------------------------
# search_text
# ---------------------------------------------------------------------------

def test_given_a_text_query_when_searching_then_calls_client_and_returns_sorted_place_results():
    # Given
    mock_client = Mock()
    mock_client.search_text.return_value = _places_response(("Pizza Place", 4.2))
    service = PlaceSearchService(google_places_client=mock_client)
    polygon = _square_polygon()

    # When
    results = service.search_text(text="pizza", search_area=polygon, types=["restaurant"])

    # Then
    assert results == [PlaceResult(name="Pizza Place", rating=4.2)]

    call_args = mock_client.search_text.call_args
    assert call_args.kwargs["text"] == "pizza"
    assert isinstance(call_args.kwargs["location_data"], PlaceSearchLocationData)
    assert call_args.kwargs["types"] == ["restaurant"]
