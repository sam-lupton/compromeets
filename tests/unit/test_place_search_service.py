from unittest.mock import Mock

import pytest
from shapely.geometry import Polygon

from compromeets.models.domain import PlaceSearchLocationData
from compromeets.services.place_search_service import PlaceSearchService


def test_overlap_to_location_data_calculates_centroid_and_radius():
    mock_client = Mock()
    service = PlaceSearchService(google_places_client=mock_client)

    # Create a simple square polygon
    polygon = Polygon([(-0.1, 51.5), (-0.08, 51.5), (-0.08, 51.52), (-0.1, 51.52)])

    location_data = service.overlap_to_location_data(polygon)

    assert isinstance(location_data, PlaceSearchLocationData)
    assert location_data.latitude == pytest.approx(51.51, abs=0.01)
    assert location_data.longitude == pytest.approx(-0.09, abs=0.01)
    assert location_data.radius > 0
    assert isinstance(location_data.radius, int)


def test_sort_places_sorts_by_rating_descending():
    mock_client = Mock()
    service = PlaceSearchService(google_places_client=mock_client)

    results = {
        "places": [
            {"displayName": {"text": "Place A"}, "rating": 3.5},
            {"displayName": {"text": "Place B"}, "rating": 4.5},
            {"displayName": {"text": "Place C"}, "rating": 4.0},
        ]
    }

    sorted_places = service.sort_places(results)

    assert len(sorted_places) == 3
    assert sorted_places[0] == ("Place B", 4.5)
    assert sorted_places[1] == ("Place C", 4.0)
    assert sorted_places[2] == ("Place A", 3.5)


def test_sort_places_handles_missing_ratings():
    mock_client = Mock()
    service = PlaceSearchService(google_places_client=mock_client)

    results = {
        "places": [
            {"displayName": {"text": "Place A"}, "rating": 4.0},
            {"displayName": {"text": "Place B"}},  # No rating
            {"displayName": {"text": "Place C"}, "rating": 5.0},
        ]
    }

    sorted_places = service.sort_places(results)

    assert sorted_places[0] == ("Place C", 5.0)
    assert sorted_places[1] == ("Place A", 4.0)
    assert sorted_places[2] == ("Place B", 0)


def test_search_nearby_calls_client_and_sorts_results():
    mock_client = Mock()
    mock_client.search_nearby.return_value = {
        "places": [
            {"displayName": {"text": "Pub A"}, "rating": 4.0},
            {"displayName": {"text": "Pub B"}, "rating": 4.5},
        ]
    }

    service = PlaceSearchService(google_places_client=mock_client)
    polygon = Polygon([(-0.1, 51.5), (-0.08, 51.5), (-0.08, 51.52), (-0.1, 51.52)])

    results = service.search_nearby(search_area=polygon, types=["pub"])

    assert len(results) == 2
    assert results[0] == ("Pub B", 4.5)
    assert results[1] == ("Pub A", 4.0)

    mock_client.search_nearby.assert_called_once()
    call_args = mock_client.search_nearby.call_args
    assert isinstance(call_args.kwargs["location_data"], PlaceSearchLocationData)
    assert call_args.kwargs["types"] == ["pub"]


def test_search_text_calls_client_with_text_query():
    mock_client = Mock()
    mock_client.search_text.return_value = {
        "places": [
            {"displayName": {"text": "Pizza Place"}, "rating": 4.2},
        ]
    }

    service = PlaceSearchService(google_places_client=mock_client)
    polygon = Polygon([(-0.1, 51.5), (-0.08, 51.5), (-0.08, 51.52), (-0.1, 51.52)])

    results = service.search_text(text="pizza", search_area=polygon, types=["restaurant"])

    assert len(results) == 1
    assert results[0] == ("Pizza Place", 4.2)

    mock_client.search_text.assert_called_once()
    call_args = mock_client.search_text.call_args
    assert call_args.kwargs["text"] == "pizza"
    assert isinstance(call_args.kwargs["location_data"], PlaceSearchLocationData)
    assert call_args.kwargs["types"] == ["restaurant"]
