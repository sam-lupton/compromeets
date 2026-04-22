from typing import cast

import geopandas as gpd
from shapely.geometry.point import Point


class PostcodeResolver:
    def __init__(self, postcodes_gdf: gpd.GeoDataFrame) -> None:
        self.postcodes_gdf = postcodes_gdf
        self.postcodes_gdf["pcds_normalized"] = self.postcodes_gdf["pcds"].str.replace(" ", "").str.upper()

    def postcode_to_point(self, postcode: str) -> Point:
        normalized_postcode = postcode.replace(" ", "").upper()

        matches = self.postcodes_gdf[self.postcodes_gdf.pcds_normalized == normalized_postcode]

        if len(matches) == 0:
            raise ValueError(
                f"Postcode '{postcode}' not found in the dataset. "
                f"Please check the postcode is valid and in the correct format."
            )

        return cast(Point, matches.geometry.values[0])
