import datetime

import geopandas as gpd
import pandas as pd
import r5py

from compromeets.services.postcode_resolver import PostcodeResolver
from compromeets.services.travel_time_service import TravelTimeService


def test_max_travel_time_between_postcodes_returns_the_maximum(
    monkeypatch, postcode_resolver: PostcodeResolver, transport_network
):
    # Given
    captured: dict[str, object] = {}

    def fake_travel_time_matrix(**kwargs):
        captured.update(kwargs)
        return pd.DataFrame({"travel_time": [12.0, 5.0, 31.5]})

    monkeypatch.setattr(r5py, "TravelTimeMatrix", fake_travel_time_matrix)
    service = TravelTimeService(postcode_resolver=postcode_resolver, transport_network=transport_network)  # type: ignore[arg-type]

    # When
    result = service.max_travel_time_between_postcodes(["AA1 1AA", "BB1 1BB", "CC1 1CC"])

    # Then
    assert result == 31.5
    assert captured["transport_network"] is transport_network


def test_max_travel_time_deduplicates_postcodes_before_routing(
    monkeypatch, postcode_resolver: PostcodeResolver, postcodes_gdf, transport_network
):
    # Given — duplicate postcode in input
    captured: dict[str, object] = {}

    def fake_travel_time_matrix(**kwargs):
        captured.update(kwargs)
        return pd.DataFrame({"travel_time": [1.0]})

    monkeypatch.setattr(r5py, "TravelTimeMatrix", fake_travel_time_matrix)
    service = TravelTimeService(postcode_resolver=postcode_resolver, transport_network=transport_network)  # type: ignore[arg-type]

    # When
    service.max_travel_time_between_postcodes(["AA1 1AA", "AA1 1AA", "BB1 1BB"])

    # Then — only 2 unique origins/destinations, not 3
    origins = captured["origins"]
    destinations = captured["destinations"]
    assert isinstance(origins, gpd.GeoDataFrame)
    assert isinstance(destinations, gpd.GeoDataFrame)
    assert len(origins) == 2
    assert len(destinations) == 2

    origin_coords = {(p.x, p.y) for p in origins.geometry}
    aa = postcodes_gdf[postcodes_gdf.pcds == "AA1 1AA"].geometry.values[0]
    bb = postcodes_gdf[postcodes_gdf.pcds == "BB1 1BB"].geometry.values[0]
    assert origin_coords == {(aa.x, aa.y), (bb.x, bb.y)}


def test_max_travel_time_forwards_custom_departure_time(monkeypatch, postcodes_gdf, transport_network):
    # Given
    captured: dict[str, object] = {}

    def fake_travel_time_matrix(**kwargs):
        captured.update(kwargs)
        return pd.DataFrame({"travel_time": [7.0]})

    monkeypatch.setattr(r5py, "TravelTimeMatrix", fake_travel_time_matrix)
    service = TravelTimeService(
        postcode_resolver=PostcodeResolver(postcodes_gdf=postcodes_gdf),
        transport_network=transport_network,  # type: ignore[arg-type]
    )
    custom_departure = datetime.datetime(2026, 3, 10, 9, 15)

    # When
    service.max_travel_time_between_postcodes(["AA1 1AA", "BB1 1BB"], departure_time=custom_departure)

    # Then
    assert captured["departure"] == custom_departure
