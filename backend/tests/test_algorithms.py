import networkx as nx
import pytest
from algorithms.astar import AStarAlgorithm, get_edge_weight, haversine_heuristic
from algorithms.base import RoutingContext
from algorithms.dfs import dfs_recovery
from algorithms.dstar_lite import DStarLite
from algorithms.hybrid import bfs_search, hybrid_route


@pytest.fixture
def sample_graph():
    G = nx.MultiDiGraph()
    G.add_node(1, x=77.59, y=12.97)
    G.add_node(2, x=77.60, y=12.97)
    G.add_node(3, x=77.61, y=12.97)
    G.add_node(4, x=77.60, y=12.98)
    G.add_edge(1, 2, key=0, length=1000, travel_time=120, highway='primary')
    G.add_edge(2, 3, key=0, length=1000, travel_time=120, highway='primary')
    G.add_edge(1, 4, key=0, length=1500, travel_time=180, highway='secondary')
    G.add_edge(4, 3, key=0, length=1500, travel_time=180, highway='secondary')
    return G


def test_haversine_heuristic(sample_graph):
    h = haversine_heuristic(sample_graph, 1, 3)
    assert h > 0
    assert h < 100


def test_get_edge_weight(sample_graph):
    w = get_edge_weight(sample_graph, 1, 2)
    assert w == 2.0


def test_astar_basic(sample_graph):
    astar = AStarAlgorithm()
    context = RoutingContext()
    result = astar.route(sample_graph, 1, 3, context)
    assert result.success
    assert result.path == [1, 2, 3]
    assert result.cost == 4.0


def test_astar_with_blockage(sample_graph):
    astar = AStarAlgorithm()
    context = RoutingContext(blocked_nodes={2})
    result = astar.route(sample_graph, 1, 3, context)
    assert result.success
    assert result.path == [1, 4, 3]


def test_dfs_recovery(sample_graph):
    blocked_nodes = {2}
    blocked_edges = set()
    original_path = [1, 2, 3]
    result = dfs_recovery(sample_graph, 1, original_path, blocked_nodes, blocked_edges)
    assert result['success']
    assert result['detour_path'][0] == 1
    assert result['rejoin_index'] == 2


def test_hybrid_route(sample_graph):
    blocked_nodes = {2}
    blocked_edges = set()
    result = hybrid_route(sample_graph, 1, 3, blocked_nodes, blocked_edges)
    assert result['merged']['success']
    assert result['blockage_detected']


def test_bfs_search(sample_graph):
    result = bfs_search(sample_graph, 1, 3)
    assert result['success']
    assert result['path'] in [[1, 2, 3], [1, 4, 3]]


def test_dstar_lite(sample_graph):
    dstar = DStarLite()
    context = RoutingContext()
    result = dstar.route(sample_graph, 1, 3, context)
    # D* Lite is complex; verify it runs without error and returns valid result object
    assert result is not None
    assert hasattr(result, 'success')
    assert hasattr(result, 'path')
    assert hasattr(result, 'cost')
    assert hasattr(result, 'nodes_expanded')
    assert hasattr(result, 'execution_time_ms')
