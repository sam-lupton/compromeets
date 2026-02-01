import datetime

import geopandas as gpd
import r5py
from shapely.geometry.point import Point

from compromeets.services.postcode_resolver import PostcodeResolver


class IsochroneService:
    def __init__(
        self,
        postcode_resolver: PostcodeResolver,
        transport_network: r5py.TransportNetwork,
    ):
        self.postcode_resolver = postcode_resolver
        self.transport_network = transport_network

    def postcodes_to_isochrones(
        self,
        postcodes: list[str],
        departure_time: datetime.datetime = datetime.datetime(2026, 2, 1, 8, 0),
        travel_times: list[float] = [15.0, 30.0, 45.0],
    ) -> tuple[r5py.Isochrones, gpd.GeoDataFrame]:
        origin_points: list[Point] = [self.postcode_resolver.postcode_to_point(postcode) for postcode in postcodes]
        origins_gdf = gpd.GeoDataFrame(
            {"id": [f"origin{i}" for i in range(len(origin_points))]},
            geometry=origin_points,
            crs="EPSG:4326",
        )

        isochrones = r5py.Isochrones(
            transport_network=self.transport_network,
            origins=origins_gdf,
            departure=departure_time,  # Must match GTFS service times - using a date with active service
            transport_modes=[r5py.TransportMode.TRANSIT, r5py.TransportMode.WALK],
            isochrones=travel_times,
        )

        return isochrones, origins_gdf
