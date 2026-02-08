import pytest
from shapely.geometry.point import Point

from compromeets.services.postcode_resolver import PostcodeResolver


def test_postcode_to_point_returns_correct_geometry(postcodes_gdf):
    resolver = PostcodeResolver(postcodes_gdf=postcodes_gdf)
    point = resolver.postcode_to_point("AA1 1AA")

    assert isinstance(point, Point)
    assert point.x == -0.10
    assert point.y == 51.50


def test_postcode_to_point_returns_different_point_for_different_postcode(postcodes_gdf):
    resolver = PostcodeResolver(postcodes_gdf=postcodes_gdf)
    point_a = resolver.postcode_to_point("AA1 1AA")
    point_b = resolver.postcode_to_point("BB1 1BB")

    assert not point_a.equals(point_b)
    assert point_b.x == -0.11
    assert point_b.y == 51.51


def test_postcode_to_point_raises_value_error_for_missing_postcode(postcodes_gdf):
    resolver = PostcodeResolver(postcodes_gdf=postcodes_gdf)
    with pytest.raises(ValueError):
        resolver.postcode_to_point("ZZ9 9ZZ")


def test_postcode_to_point_case_insensitive(postcodes_gdf):
    resolver = PostcodeResolver(postcodes_gdf=postcodes_gdf)
    point = resolver.postcode_to_point("aa1 1aa")
    assert point.x == -0.10
    assert point.y == 51.50
