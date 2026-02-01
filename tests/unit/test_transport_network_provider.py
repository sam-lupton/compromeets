from pathlib import Path
from unittest.mock import Mock, patch

from compromeets.services.transport_network_provider import TransportNetworkProvider


@patch("compromeets.services.transport_network_provider.r5py.TransportNetwork")
def test_get_transport_network_constructs_network_with_correct_paths(mock_transport_network_class):
    mock_network = Mock()
    mock_transport_network_class.return_value = mock_network

    osm_path = Path("/path/to/osm.pbf")
    gtfs_path = Path("/path/to/gtfs.zip")

    provider = TransportNetworkProvider(osm_path=osm_path, gtfs_path=gtfs_path)
    result = provider.get_transport_network()

    assert result is mock_network
    mock_transport_network_class.assert_called_once_with(
        osm_pbf=osm_path,
        gtfs=[gtfs_path],
    )


@patch("compromeets.services.transport_network_provider.r5py.TransportNetwork")
def test_get_transport_network_stores_paths(mock_transport_network_class):
    osm_path = Path("/path/to/osm.pbf")
    gtfs_path = Path("/path/to/gtfs.zip")

    provider = TransportNetworkProvider(osm_path=osm_path, gtfs_path=gtfs_path)

    assert provider.osm_path == osm_path
    assert provider.gtfs_path == gtfs_path


@patch("compromeets.services.transport_network_provider.r5py.TransportNetwork")
def test_get_transport_network_can_be_called_multiple_times(mock_transport_network_class):
    # Each call should create a new network
    mock_network1 = Mock()
    mock_network2 = Mock()
    mock_transport_network_class.side_effect = [mock_network1, mock_network2]

    provider = TransportNetworkProvider(
        osm_path=Path("/path/to/osm.pbf"),
        gtfs_path=Path("/path/to/gtfs.zip"),
    )

    result1 = provider.get_transport_network()
    result2 = provider.get_transport_network()

    assert result1 is mock_network1
    assert result2 is mock_network2
    assert mock_transport_network_class.call_count == 2
