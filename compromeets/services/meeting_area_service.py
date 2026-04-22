import geopandas as gpd
from r5py import Isochrones
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union


def _largest_polygon(geom: BaseGeometry) -> Polygon:
    """Return the largest Polygon from any geometry, raising if none exists."""
    if geom.is_empty:
        raise ValueError("Isochrone overlap is empty — participants have no reachable common area")
    if isinstance(geom, Polygon):
        return geom
    # MultiPolygon or GeometryCollection — pick the largest polygon component
    candidates = [g for g in getattr(geom, "geoms", []) if isinstance(g, Polygon)]
    if not candidates:
        raise ValueError(f"Isochrone overlap produced no polygon (got {geom.geom_type})")
    return max(candidates, key=lambda p: p.area)


class MeetingAreaService:
    def find_meeting_area(
        self,
        isochrones: Isochrones,
    ) -> tuple[Polygon, gpd.GeoDataFrame]:
        polygons: list[BaseGeometry] = []

        for iso in isochrones.geometry:
            poly = unary_union(iso).buffer(0.0001).convex_hull
            polygons.append(poly)

        if len(polygons) == 0:
            raise ValueError("No valid isochrones found for any person")

        # Find the intersection of all polygons
        raw_overlap: BaseGeometry = polygons[0]
        for poly in polygons[1:]:
            raw_overlap = raw_overlap.intersection(poly)

        overlap_polygon = _largest_polygon(raw_overlap)

        overlap_gdf = gpd.GeoDataFrame({"description": ["Overlap area"]}, geometry=[overlap_polygon], crs="EPSG:4326")

        print(f"Overlap area: {overlap_polygon.area * 111000 * 111000:.2f} square meters")
        print(f"Overlap exists: {not overlap_polygon.is_empty}")

        return overlap_polygon, overlap_gdf
