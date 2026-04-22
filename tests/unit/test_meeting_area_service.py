import geopandas as gpd
import pytest
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry

from compromeets.services.meeting_area_service import MeetingAreaService


def test_find_meeting_area_with_overlapping_polygons():
    # Create mock isochrones with overlapping polygons
    poly1 = Polygon([(-0.1, 51.5), (-0.08, 51.5), (-0.08, 51.52), (-0.1, 51.52)])
    poly2 = Polygon([(-0.09, 51.49), (-0.07, 51.49), (-0.07, 51.51), (-0.09, 51.51)])

    mock_isochrones = gpd.GeoDataFrame(
        {"id": ["origin0", "origin1"]},
        geometry=[poly1, poly2],
        crs="EPSG:4326",
    )

    service = MeetingAreaService()
    overlap_polygon, overlap_gdf = service.find_meeting_area(isochrones=mock_isochrones)

    assert isinstance(overlap_polygon, BaseGeometry)
    assert not overlap_polygon.is_empty
    assert isinstance(overlap_gdf, gpd.GeoDataFrame)
    assert len(overlap_gdf) == 1
    assert overlap_gdf.crs.to_string() == "EPSG:4326"


def test_find_meeting_area_with_single_polygon():
    poly1 = Polygon([(-0.1, 51.5), (-0.08, 51.5), (-0.08, 51.52), (-0.1, 51.52)])

    mock_isochrones = gpd.GeoDataFrame(
        {"id": ["origin0"]},
        geometry=[poly1],
        crs="EPSG:4326",
    )

    service = MeetingAreaService()
    overlap_polygon, overlap_gdf = service.find_meeting_area(isochrones=mock_isochrones)

    assert isinstance(overlap_polygon, BaseGeometry)
    assert not overlap_polygon.is_empty


def test_find_meeting_area_with_no_overlap():
    # Create non-overlapping polygons
    poly1 = Polygon([(-0.1, 51.5), (-0.08, 51.5), (-0.08, 51.52), (-0.1, 51.52)])
    poly2 = Polygon([(-0.05, 51.6), (-0.03, 51.6), (-0.03, 51.62), (-0.05, 51.62)])

    mock_isochrones = gpd.GeoDataFrame(
        {"id": ["origin0", "origin1"]},
        geometry=[poly1, poly2],
        crs="EPSG:4326",
    )

    service = MeetingAreaService()
    overlap_polygon, overlap_gdf = service.find_meeting_area(isochrones=mock_isochrones)

    # Even with no overlap, a result is returned (it will be empty)
    assert isinstance(overlap_polygon, BaseGeometry)
    assert overlap_polygon.is_empty


def test_find_meeting_area_raises_for_empty_isochrones():
    mock_isochrones = gpd.GeoDataFrame(
        {"id": []},
        geometry=[],
        crs="EPSG:4326",
    )

    service = MeetingAreaService()
    with pytest.raises(ValueError, match="No valid isochrones found"):
        service.find_meeting_area(isochrones=mock_isochrones)
