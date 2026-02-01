from unittest.mock import Mock

import geopandas as gpd
from shapely.geometry import Polygon

from compromeets.services.suggest_service import SuggestService


def test_suggest_places_orchestrates_full_flow():
    # Mock dependencies
    mock_isochrone_service = Mock()
    mock_meeting_area_service = Mock()
    mock_place_search_service = Mock()
    mock_google_places_client = Mock()

    # Setup return values
    mock_isochrones = object()
    mock_origins_gdf = gpd.GeoDataFrame()
    mock_isochrone_service.postcodes_to_isochrones.return_value = (mock_isochrones, mock_origins_gdf)

    mock_polygon = Polygon([(-0.1, 51.5), (-0.08, 51.5), (-0.08, 51.52), (-0.1, 51.52)])
    mock_gdf = gpd.GeoDataFrame()
    mock_meeting_area_service.find_meeting_area.return_value = (mock_polygon, mock_gdf)

    expected_places = [("Pub A", 4.5), ("Pub B", 4.0)]
    mock_place_search_service.search_nearby.return_value = expected_places

    # Test
    service = SuggestService(
        isochrone_service=mock_isochrone_service,
        meeting_area_service=mock_meeting_area_service,
        place_search_service=mock_place_search_service,
        google_places_client=mock_google_places_client,
    )

    postcodes = ["E14 2DF", "N7 0AA"]
    types = ["pub"]

    result = service.suggest_places(postcodes=postcodes, types=types)

    # Assertions
    assert result == expected_places

    mock_isochrone_service.postcodes_to_isochrones.assert_called_once_with(postcodes)
    mock_meeting_area_service.find_meeting_area.assert_called_once_with(isochrones=mock_isochrones)
    mock_place_search_service.search_nearby.assert_called_once_with(search_area=mock_polygon, types=types)


def test_suggest_places_passes_through_types():
    mock_isochrone_service = Mock()
    mock_meeting_area_service = Mock()
    mock_place_search_service = Mock()
    mock_google_places_client = Mock()

    mock_isochrones = object()
    mock_isochrone_service.postcodes_to_isochrones.return_value = (mock_isochrones, None)

    mock_polygon = Polygon([(-0.1, 51.5), (-0.08, 51.5), (-0.08, 51.52), (-0.1, 51.52)])
    mock_meeting_area_service.find_meeting_area.return_value = (mock_polygon, None)

    mock_place_search_service.search_nearby.return_value = []

    service = SuggestService(
        isochrone_service=mock_isochrone_service,
        meeting_area_service=mock_meeting_area_service,
        place_search_service=mock_place_search_service,
        google_places_client=mock_google_places_client,
    )

    service.suggest_places(postcodes=["E14 2DF"], types=["restaurant", "cafe"])

    call_args = mock_place_search_service.search_nearby.call_args
    assert call_args.kwargs["types"] == ["restaurant", "cafe"]
