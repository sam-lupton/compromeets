from pydantic import BaseModel


class PlaceSearchLocationData(BaseModel):
    """Data for searching for places nearby a location in Google Places API"""

    latitude: float
    longitude: float
    radius: int

    def location_dict(self) -> dict[str, float]:
        return {"latitude": self.latitude, "longitude": self.longitude}


# --- Google Places API contract types ---
# These models define the contract between PlaceSearchService (consumer)
# and GooglePlacesClient (provider). Any change to these shapes is a breaking contract change.


class DisplayName(BaseModel):
    text: str


class GooglePlaceRaw(BaseModel):
    """A single place entry as returned by the Google Places API."""

    displayName: DisplayName
    rating: float = 0.0
    userRatingCount: int = 0


class GooglePlacesResponse(BaseModel):
    """Full response envelope from the Google Places API.

    Defaults places to an empty list so a {} response (no results) parses cleanly.
    """

    places: list[GooglePlaceRaw] = []


# --- Clean domain output ---


class PlaceResult(BaseModel):
    """A processed meeting-place result returned by PlaceSearchService."""

    name: str
    rating: float
