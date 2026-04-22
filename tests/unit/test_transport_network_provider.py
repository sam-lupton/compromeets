from pathlib import Path
from unittest.mock import Mock, patch

from compromeets.services.transport_network_provider import TransportNetworkProvider


@patch("compromeets.services.transport_network_provider.r5py.TransportNetwork")
def test_get_transport_network_returns_network_built_from_given_paths(mock_transport_network_class):
    mock_network = Mock()
    mock_transport_network_class.return_value = mock_network

    provider = TransportNetworkProvider(
        osm_path=Path("/path/to/osm.pbf"),
        gtfs_path=Path("/path/to/gtfs.zip"),
    )
    result = provider.get_transport_network()

    assert result is mock_network
    mock_transport_network_class.assert_called_once_with(
        osm_pbf=Path("/path/to/osm.pbf"),
        gtfs=[Path("/path/to/gtfs.zip")],
    )


@patch("compromeets.services.transport_network_provider.r5py.TransportNetwork")
def test_get_transport_network_builds_a_new_network_on_each_call(mock_transport_network_class):
    mock_network1, mock_network2 = Mock(), Mock()
    mock_transport_network_class.side_effect = [mock_network1, mock_network2]

    provider = TransportNetworkProvider(
        osm_path=Path("/path/to/osm.pbf"),
        gtfs_path=Path("/path/to/gtfs.zip"),
    )

    assert provider.get_transport_network() is mock_network1
    assert provider.get_transport_network() is mock_network2
