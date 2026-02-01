# Calls GooglePlacesClient to search for places nearby a location
# Handles multi-centre search, pagination/retries/backoff, deduping + canonicalisation, and rankings

from shapely.geometry.base import BaseGeometry
from shapely.geometry.point import Point

from compromeets.clients.google_places_client import GooglePlacesClient
from compromeets.models.domain import PlaceSearchLocationData


class PlaceSearchService:
    def __init__(self, google_places_client: GooglePlacesClient):
        self.google_places_client = google_places_client

    def sort_places(self, results: dict) -> list[tuple[str, float]]:
        """Sort places by rating"""
        return sorted(
            [(place["displayName"]["text"], place.get("rating", 0)) for place in results["places"]],
            key=lambda x: x[1],
            reverse=True,
        )

    def overlap_to_location_data(self, overlap: BaseGeometry) -> PlaceSearchLocationData:
        centroid = overlap.centroid
        center_lat = centroid.y
        center_lng = centroid.x

        # Calculate approximate radius in meters
        # Get the distance from center to farthest point

        max_distance = (
            max(
                [Point(center_lng, center_lat).distance(Point(coord[0], coord[1])) for coord in overlap.exterior.coords]
            )
            * 111000
        )  # Rough conversion to meters (1 degree ≈ 111km)

        # For Google Maps Nearby Search
        radius = int(max_distance)

        return PlaceSearchLocationData(latitude=center_lat, longitude=center_lng, radius=radius)

    def search_nearby(self, search_area: BaseGeometry, types: list[str]) -> list[tuple[str, float]]:
        location_data = self.overlap_to_location_data(search_area)
        results = self.google_places_client.search_nearby(location_data=location_data, types=types)
        return self.sort_places(results)

    def search_text(self, text: str, search_area: BaseGeometry, types: list[str]) -> list[tuple[str, float]]:
        location_data = self.overlap_to_location_data(search_area)
        results = self.google_places_client.search_text(text=text, location_data=location_data, types=types)
        return self.sort_places(results)
