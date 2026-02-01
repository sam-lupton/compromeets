import geopandas as gpd
import pytest
from shapely.geometry import Point


@pytest.fixture
def postcodes_gdf() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {
            "pcds": ["AA1 1AA", "BB1 1BB", "CC1 1CC"],
            "geometry": [
                Point(-0.10, 51.50),
                Point(-0.11, 51.51),
                Point(-0.12, 51.52),
            ],
        },
        crs="EPSG:4326",
    )


@pytest.fixture
def transport_network() -> object:
    return object()
