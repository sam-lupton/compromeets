# Pydantic models for the domain

from pydantic import BaseModel


class PlaceSearchLocationData(BaseModel):
    """Data for searching for places nearby a location in Google Places API"""

    latitude: float
    longitude: float
    radius: int

    def location_dict(self) -> dict[str, float]:
        return {"latitude": self.latitude, "longitude": self.longitude}
