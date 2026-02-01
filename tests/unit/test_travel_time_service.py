import datetime

import geopandas as gpd
import pandas as pd
import pytest
import r5py
from shapely.geometry.point import Point

from compromeets.services.postcode_resolver import PostcodeResolver
from compromeets.services.travel_time_service import TravelTimeService


def test_postcode_to_point_returns_geometry(postcode_resolver: PostcodeResolver, postcodes_gdf):
    point = postcode_resolver.postcode_to_point("AA1 1AA")

    assert isinstance(point, Point)
    assert point.equals(postcodes_gdf[postcodes_gdf.pcds == "AA1 1AA"].geometry.values[0])


def test_postcode_to_point_raises_for_missing_postcode(postcode_resolver: PostcodeResolver):
    with pytest.raises(IndexError):
        postcode_resolver.postcode_to_point("ZZ9 9ZZ")


def test_max_travel_time_between_postcodes_returns_max_and_wires_matrix_call(
    monkeypatch, postcode_resolver: PostcodeResolver, transport_network
):
    captured: dict[str, object] = {}

    def fake_travel_time_matrix(**kwargs):
        captured.update(kwargs)
        return pd.DataFrame({"travel_time": [12.0, 5.0, 31.5]})

    monkeypatch.setattr(r5py, "TravelTimeMatrix", fake_travel_time_matrix)

    service = TravelTimeService(postcode_resolver=postcode_resolver, transport_network=transport_network)  # type: ignore[arg-type]
    result = service.max_travel_time_between_postcodes(["AA1 1AA", "BB1 1BB", "CC1 1CC"])

    assert result == 31.5
    assert captured["transport_network"] is transport_network
    assert isinstance(captured["origins"], gpd.GeoDataFrame)
    assert isinstance(captured["destinations"], gpd.GeoDataFrame)
    assert captured["departure"] == datetime.datetime(2026, 2, 1, 8, 0)
    assert captured["transport_modes"] == [r5py.TransportMode.TRANSIT, r5py.TransportMode.WALK]


def test_max_travel_time_between_postcodes_dedupes_postcodes(
    monkeypatch, postcode_resolver: PostcodeResolver, postcodes_gdf, transport_network
):
    captured: dict[str, object] = {}

    def fake_travel_time_matrix(**kwargs):
        captured.update(kwargs)
        return pd.DataFrame({"travel_time": [1.0]})

    monkeypatch.setattr(r5py, "TravelTimeMatrix", fake_travel_time_matrix)

    service = TravelTimeService(postcode_resolver=postcode_resolver, transport_network=transport_network)  # type: ignore[arg-type]
    service.max_travel_time_between_postcodes(["AA1 1AA", "AA1 1AA", "BB1 1BB"])

    origins = captured["origins"]
    destinations = captured["destinations"]
    assert isinstance(origins, gpd.GeoDataFrame)
    assert isinstance(destinations, gpd.GeoDataFrame)
    assert len(origins) == 2
    assert len(destinations) == 2

    origin_coords = {(p.x, p.y) for p in origins.geometry}
    aa = postcodes_gdf[postcodes_gdf.pcds == "AA1 1AA"].geometry.values[0]
    bb = postcodes_gdf[postcodes_gdf.pcds == "BB1 1BB"].geometry.values[0]
    expected_coords = {
        (aa.x, aa.y),
        (bb.x, bb.y),
    }
    assert origin_coords == expected_coords


def test_max_travel_time_between_postcodes_allows_custom_departure_time(monkeypatch, postcodes_gdf, transport_network):
    captured: dict[str, object] = {}

    def fake_travel_time_matrix(**kwargs):
        captured.update(kwargs)
        return pd.DataFrame({"travel_time": [7.0]})

    monkeypatch.setattr(r5py, "TravelTimeMatrix", fake_travel_time_matrix)

    service = TravelTimeService(
        postcode_resolver=PostcodeResolver(postcodes_gdf=postcodes_gdf), transport_network=transport_network
    )  # type: ignore[arg-type]
    custom_departure = datetime.datetime(2026, 3, 10, 9, 15)
    service.max_travel_time_between_postcodes(["AA1 1AA", "BB1 1BB"], departure_time=custom_departure)

    assert captured["departure"] == custom_departure
