# Calls GooglePlacesClient to search for places nearby a location
# Handles multi-centre search, pagination/retries/backoff, deduping + canonicalisation, and rankings

from shapely.geometry.base import BaseGeometry
from shapely.geometry.point import Point

from compromeets.clients.google_places_client import GooglePlacesClient
from compromeets.models.domain import PlaceSearchLocationData


class PlaceSearchService:
    # Valid Google Places API types
    VALID_GOOGLE_TYPES = {
        "restaurant", "cafe", "bar", "pub", "night_club", "bakery", "meal_takeaway",
        "meal_delivery", "park", "tourist_attraction", "museum", "art_gallery",
        "shopping_mall", "movie_theater", "bowling_alley", "amusement_park",
        "aquarium", "zoo", "library", "gym", "spa", "stadium", "casino"
    }
    
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

    def is_valid_google_type(self, venue_type: str) -> bool:
        """Check if a venue type is a valid Google Places API type"""
        return venue_type.lower() in self.VALID_GOOGLE_TYPES
    
    def search_nearby(self, search_area: BaseGeometry, types: list[str]) -> list[tuple[str, float]]:
        """
        Search for places using Google Places API.
        Automatically handles custom venue types by using text search.
        """
        location_data = self.overlap_to_location_data(search_area)
        
        # Separate valid Google types from custom types
        valid_types = [t for t in types if self.is_valid_google_type(t)]
        custom_types = [t for t in types if not self.is_valid_google_type(t)]
        
        # If we have custom types, use text search instead
        if custom_types:
            # Use the custom type as a text query
            text_query = " or ".join(custom_types)
            results = self.google_places_client.search_text(
                text=text_query, 
                location_data=location_data, 
                types=valid_types if valid_types else None
            )
        else:
            # Use standard nearby search with valid types
            results = self.google_places_client.search_nearby(location_data=location_data, types=valid_types)
        
        return self.sort_places(results)

    def search_text(self, text: str, search_area: BaseGeometry, types: list[str] | None = None) -> list[tuple[str, float]]:
        location_data = self.overlap_to_location_data(search_area)
        
        # Filter to only valid Google types if provided
        valid_types = None
        if types:
            valid_types = [t for t in types if self.is_valid_google_type(t)]
            if not valid_types:
                valid_types = None
        
        results = self.google_places_client.search_text(text=text, location_data=location_data, types=valid_types)
        return self.sort_places(results)
