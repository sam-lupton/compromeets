import datetime

import geopandas as gpd
import r5py

from compromeets.services.isochrone_service import IsochroneService


def test_postcodes_to_isochrones_builds_origins_gdf_and_calls_r5py(monkeypatch, postcode_resolver, transport_network):
    captured: dict[str, object] = {}
    sentinel_isochrones = object()

    def fake_isochrones(**kwargs):
        captured.update(kwargs)
        return sentinel_isochrones

    monkeypatch.setattr(r5py, "Isochrones", fake_isochrones)

    service = IsochroneService(postcode_resolver=postcode_resolver, transport_network=transport_network)
    departure = datetime.datetime(2026, 2, 1, 8, 0)
    travel_times = [15.0, 30.0]

    isochrones, origins_gdf = service.postcodes_to_isochrones(
        postcodes=["AA1 1AA", "BB1 1BB", "CC1 1CC"],
        departure_time=departure,
        travel_times=travel_times,
    )

    assert isochrones is sentinel_isochrones
    assert isinstance(origins_gdf, gpd.GeoDataFrame)
    assert list(origins_gdf.columns) == ["id", "geometry"]
    assert len(origins_gdf) == 3
    assert origins_gdf.crs is not None
    assert origins_gdf.crs.to_string() == "EPSG:4326"

    assert captured["transport_network"] is transport_network
    assert captured["origins"] is origins_gdf
    assert captured["departure"] == departure
    assert captured["isochrones"] == travel_times
    assert captured["transport_modes"] == [r5py.TransportMode.TRANSIT, r5py.TransportMode.WALK]
