from pathlib import Path

import r5py


class TransportNetworkProvider:
    def __init__(
        self,
        osm_path: Path,
        gtfs_path: Path,
    ):
        self.osm_path = osm_path
        self.gtfs_path = gtfs_path

    def get_transport_network(self) -> r5py.TransportNetwork:
        return r5py.TransportNetwork(
            osm_pbf=self.osm_path,
            gtfs=[self.gtfs_path],
        )
