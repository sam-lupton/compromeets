import geopandas as gpd
from shapely.geometry.point import Point


class PostcodeResolver:
    def __init__(self, postcodes_gdf: gpd.GeoDataFrame) -> None:
        self.postcodes_gdf = postcodes_gdf

    def postcode_to_point(self, postcode: str) -> Point:
        return self.postcodes_gdf[self.postcodes_gdf.pcds == postcode].geometry.values[0]  # type: ignore
