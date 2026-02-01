# Service for calculating travel times between locations based on r5py.TravelTimeMatrix

import datetime

import geopandas as gpd
import pandas as pd
import r5py
from shapely.geometry.point import Point

from compromeets.services.postcode_resolver import PostcodeResolver


class TravelTimeService:
    def __init__(
        self,
        postcode_resolver: PostcodeResolver,
        transport_network: r5py.TransportNetwork,
    ):
        self.postcode_resolver = postcode_resolver
        self.transport_network = transport_network

    def max_travel_time_between_postcodes(
        self, postcodes: list[str], departure_time: datetime.datetime = datetime.datetime(2026, 2, 1, 8, 0)
    ) -> float:
        postcode_points = [self.postcode_resolver.postcode_to_point(postcode) for postcode in set(postcodes)]
        num_points = len(postcode_points)
        origins = gpd.GeoDataFrame(
            {"id": [f"origin{i}" for i in range(num_points)]}, geometry=postcode_points, crs="EPSG:4326"
        )
        destinations = gpd.GeoDataFrame(
            {"id": [f"dest{i}" for i in range(num_points)]}, geometry=postcode_points, crs="EPSG:4326"
        )
        # Calculate travel time matrix (fastest method)
        travel_times = r5py.TravelTimeMatrix(  # type: ignore
            transport_network=self.transport_network,
            origins=origins,
            destinations=destinations,
            departure=departure_time,
            transport_modes=[r5py.TransportMode.TRANSIT, r5py.TransportMode.WALK],
        )

        return max(travel_times["travel_time"])

    def calculate_travel_times_to_destination(
        self,
        origins: list[Point],
        destination: Point,
        departure_time: datetime.datetime = datetime.datetime(2026, 2, 1, 8, 0),
    ) -> pd.Series:
        origin_gdf = gpd.GeoDataFrame(
            {"id": [f"origin{i}" for i in range(len(origins))]}, geometry=origins, crs="EPSG:4326"
        )
        destination_gdf = gpd.GeoDataFrame({"id": ["destination"]}, geometry=[destination], crs="EPSG:4326")
        travel_times = r5py.TravelTimeMatrix(  # type: ignore
            transport_network=self.transport_network,
            origins=origin_gdf,
            destinations=destination_gdf,
            departure=departure_time,
            transport_modes=[r5py.TransportMode.TRANSIT, r5py.TransportMode.WALK],
        )
        return travel_times["travel_time"]  # type: ignore
