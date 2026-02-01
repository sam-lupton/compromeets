import geopandas as gpd
from r5py import Isochrones
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union


class MeetingAreaService:
    def find_meeting_area(
        self,
        isochrones: Isochrones,
    ) -> tuple[BaseGeometry, gpd.GeoDataFrame]:
        polygons: list[BaseGeometry] = []

        for iso in isochrones.geometry:
            poly = unary_union(iso).buffer(0.0001).convex_hull
            polygons.append(poly)

        if len(polygons) == 0:
            raise ValueError("No valid isochrones found for any person")

        # Find the intersection of all polygons
        if len(polygons) == 1:
            overlap_polygon = polygons[0]
        else:
            overlap_polygon = polygons[0]
            for poly in polygons[1:]:
                overlap_polygon = overlap_polygon.intersection(poly)

        # Create a GeoDataFrame for the overlap
        overlap_gdf = gpd.GeoDataFrame({"description": ["Overlap area"]}, geometry=[overlap_polygon], crs="EPSG:4326")

        print(f"Overlap area: {overlap_polygon.area * 111000 * 111000:.2f} square meters")
        print(f"Overlap exists: {not overlap_polygon.is_empty}")

        return overlap_polygon, overlap_gdf
