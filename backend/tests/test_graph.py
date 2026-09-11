import networkx as nx
import pytest
from utils.graph_loader import (
    get_edge_weight,
    get_graph_bounds,
    get_nearest_node,
    get_node_coords,
    load_graph,
)


@pytest.fixture(scope="module")
def graph():
    return load_graph()


def test_load_graph(graph):
    assert isinstance(graph, nx.MultiDiGraph)
    assert graph.number_of_nodes() > 0
    assert graph.number_of_edges() > 0


def test_get_nearest_node(graph):
    node = get_nearest_node(graph, 12.9716, 77.5946)
    assert node in graph.nodes


def test_get_node_coords(graph):
    node = list(graph.nodes)[0]
    lat, lng = get_node_coords(graph, node)
    assert -90 <= lat <= 90
    assert -180 <= lng <= 180


def test_get_graph_bounds(graph):
    bounds = get_graph_bounds(graph)
    assert 'north' in bounds
    assert 'south' in bounds
    assert 'east' in bounds
    assert 'west' in bounds
    assert 'center_lat' in bounds
    assert 'center_lon' in bounds


def test_get_edge_weight(graph):
    u, v, _ = list(graph.edges(keys=True))[0]
    weight = get_edge_weight(graph, u, v)
    assert weight > 0
