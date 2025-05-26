import pytest
from collections import deque
from graph.currency_graph import CurrencyGraph, Edge
from path_algorithms.bellman_ford import BellmanFordFIFO

@pytest.fixture
def graph_no_cycle():
    """Graph with no cycle."""
    graph = CurrencyGraph()
    graph.add_edge(Edge("USD", "EUR", 0.5))
    graph.add_edge(Edge("EUR", "GBP", 0.5))
    return graph

@pytest.fixture
def graph_positive_cycle():
    """Graph with a positive cycle."""
    graph = CurrencyGraph()
    graph.add_edge(Edge("USD", "EUR", 0.5))
    graph.add_edge(Edge("EUR", "GBP", 0.5))
    graph.add_edge(Edge("GBP", "USD", 2.5)) 
    return graph

@pytest.fixture
def graph_negative_cycle():
    """Graph with a negative cycle."""
    graph = CurrencyGraph()
    graph.add_edge(Edge("USD", "EUR", -0.5)) # Changed to negative for clarity with name
    graph.add_edge(Edge("EUR", "GBP", -0.5))
    graph.add_edge(Edge("GBP", "USD", -0.5))  
    return graph

@pytest.fixture
def graph_zero_cycle():
    """Graph with a zero-weight cycle."""
    graph = CurrencyGraph()
    graph.add_edge(Edge("USD", "EUR", 0))
    graph.add_edge(Edge("EUR", "GBP", 0))
    graph.add_edge(Edge("GBP", "USD", 0))
    return graph

@pytest.fixture
def graph_disconnected_component():
    """Graph with a disconnected component."""
    graph = CurrencyGraph()
    graph.add_edge(Edge("USD", "EUR", 0.5))
    graph.add_edge(Edge("CAD", "JPY", 1.0)) # Disconnected part
    # Ensure all nodes are added if not implicitly by edges
    graph.add_vertex("USD")
    graph.add_vertex("EUR")
    graph.add_vertex("CAD")
    graph.add_vertex("JPY")
    graph.add_vertex("GBP") # A completely isolated node
    return graph

@pytest.fixture
def graph_all_negative_no_cycle():
    """Graph with no cycle and all negative weights."""
    graph = CurrencyGraph()
    graph.add_edge(Edge("USD", "EUR", -0.5))
    graph.add_edge(Edge("EUR", "GBP", -0.5))
    return graph

@pytest.fixture
def graph_all_zero_no_cycle():
    """Graph with no cycle and all zero weights."""
    graph = CurrencyGraph()
    graph.add_edge(Edge("USD", "EUR", 0))
    graph.add_edge(Edge("EUR", "GBP", 0))
    return graph

@pytest.fixture
def graph_single_node_no_edges():
    """Graph with a single node and no edges."""
    graph = CurrencyGraph()
    graph.add_vertex("USD")
    return graph

def test_no_cycle(graph_no_cycle: CurrencyGraph):
    """Test case for a graph with no cycle."""
    source_currency = "USD"
    bf_fifo = BellmanFordFIFO(graph_no_cycle, source_currency)
    bf_fifo.initialise(graph_no_cycle, source_currency)

    bf_fifo.weights = {("USD", "EUR"): 0.5, ("EUR", "GBP"): 0.5} # Ensure weights are present for BellmanFordFIFO
    bf_fifo.dist["USD"] = 0.0
    bf_fifo.dist["EUR"] = 0.5
    bf_fifo.dist["GBP"] = 1.0
    bf_fifo.parent["EUR"] = "USD"
    bf_fifo.parent["GBP"] = "EUR"
    
    assert not bf_fifo.detect_parent_node_cycle(graph_no_cycle, "GBP")
    assert not bf_fifo.detect_parent_node_cycle(graph_no_cycle, "EUR")
    bf_fifo.parent[source_currency] = None # As per initialise
    assert not bf_fifo.detect_parent_node_cycle(graph_no_cycle, source_currency)


def test_positive_weight_cycle(graph_positive_cycle: CurrencyGraph):
    """Test case for a graph with a positive cycle where parent pointers form a cycle."""
    source_currency = "USD"
    bf_fifo = BellmanFordFIFO(graph_positive_cycle, source_currency)
    bf_fifo.initialise(graph_positive_cycle, source_currency)

    bf_fifo.weights = {("USD", "EUR"): 0.5, ("EUR", "GBP"): 0.5, ("GBP", "USD"): 2.5}
    bf_fifo.dist["USD"] = 0.0
    bf_fifo.dist["EUR"] = 0.5
    bf_fifo.dist["GBP"] = 1.0 
    bf_fifo.parent["EUR"] = "USD"
    bf_fifo.parent["GBP"] = "EUR"
    bf_fifo.parent["USD"] = "GBP" 

    assert bf_fifo.detect_parent_node_cycle(graph_positive_cycle, "USD")
    assert bf_fifo.detect_parent_node_cycle(graph_positive_cycle, "EUR")
    assert bf_fifo.detect_parent_node_cycle(graph_positive_cycle, "GBP")

def test_negative_cycle(graph_negative_cycle: CurrencyGraph):
    """Test case for a graph with a negative cycle where parent pointers form a cycle."""
    source_currency = "USD"
    bf_fifo = BellmanFordFIFO(graph_negative_cycle, source_currency)
    bf_fifo.initialise(graph_negative_cycle, source_currency)

    bf_fifo.weights = {("USD", "EUR"): -0.5, ("EUR", "GBP"): -0.5, ("GBP", "USD"): -0.5}
    bf_fifo.dist["USD"] = 0.0 
    bf_fifo.dist["EUR"] = -0.5 
    bf_fifo.dist["GBP"] = -1.0 
    bf_fifo.parent["EUR"] = "USD"
    bf_fifo.parent["GBP"] = "EUR"
    bf_fifo.parent["USD"] = "GBP"

    assert bf_fifo.detect_parent_node_cycle(graph_negative_cycle, "USD")
    assert bf_fifo.detect_parent_node_cycle(graph_negative_cycle, "EUR")
    assert bf_fifo.detect_parent_node_cycle(graph_negative_cycle, "GBP")

def test_zero_cycle(graph_zero_cycle: CurrencyGraph):
    """Test case for a graph with a zero-weight cycle where parent pointers form a cycle."""
    source_currency = "USD"
    bf_fifo = BellmanFordFIFO(graph_zero_cycle, source_currency)
    bf_fifo.initialise(graph_zero_cycle, source_currency)

    bf_fifo.weights = {("USD", "EUR"): 0, ("EUR", "GBP"): 0, ("GBP", "USD"): 0}
    bf_fifo.dist["USD"] = 0.0
    bf_fifo.dist["EUR"] = 0.0
    bf_fifo.dist["GBP"] = 0.0
    bf_fifo.parent["EUR"] = "USD"
    bf_fifo.parent["GBP"] = "EUR"
    bf_fifo.parent["USD"] = "GBP"

    assert bf_fifo.detect_parent_node_cycle(graph_zero_cycle, "USD")
    assert bf_fifo.detect_parent_node_cycle(graph_zero_cycle, "EUR")
    assert bf_fifo.detect_parent_node_cycle(graph_zero_cycle, "GBP")

def test_all_negative_no_cycle(graph_all_negative_no_cycle: CurrencyGraph):
    """Test case for a graph with no cycle and all negative weights."""
    source_currency = "USD"
    bf_fifo = BellmanFordFIFO(graph_all_negative_no_cycle, source_currency)
    bf_fifo.initialise(graph_all_negative_no_cycle, source_currency)

    bf_fifo.weights = {("USD", "EUR"): -0.5, ("EUR", "GBP"): -0.5}
    bf_fifo.dist["USD"] = 0.0
    bf_fifo.dist["EUR"] = -0.5
    bf_fifo.dist["GBP"] = -1.0
    bf_fifo.parent["EUR"] = "USD"
    bf_fifo.parent["GBP"] = "EUR"
    bf_fifo.parent[source_currency] = None


    assert not bf_fifo.detect_parent_node_cycle(graph_all_negative_no_cycle, "GBP")
    assert not bf_fifo.detect_parent_node_cycle(graph_all_negative_no_cycle, "EUR")
    assert not bf_fifo.detect_parent_node_cycle(graph_all_negative_no_cycle, source_currency)

def test_all_zero_no_cycle(graph_all_zero_no_cycle: CurrencyGraph):
    """Test case for a graph with no cycle and all zero weights."""
    source_currency = "USD"
    bf_fifo = BellmanFordFIFO(graph_all_zero_no_cycle, source_currency)
    bf_fifo.initialise(graph_all_zero_no_cycle, source_currency)

    bf_fifo.weights = {("USD", "EUR"): 0, ("EUR", "GBP"): 0}
    bf_fifo.dist["USD"] = 0.0
    bf_fifo.dist["EUR"] = 0.0
    bf_fifo.dist["GBP"] = 0.0
    bf_fifo.parent["EUR"] = "USD"
    bf_fifo.parent["GBP"] = "EUR"
    bf_fifo.parent[source_currency] = None

    assert not bf_fifo.detect_parent_node_cycle(graph_all_zero_no_cycle, "GBP")
    assert not bf_fifo.detect_parent_node_cycle(graph_all_zero_no_cycle, "EUR")
    assert not bf_fifo.detect_parent_node_cycle(graph_all_zero_no_cycle, source_currency)

def test_bellman_ford_no_negative_cycle(graph_no_cycle: CurrencyGraph):
    """Test Bellman-Ford FIFO algorithm on a graph with no negative cycles."""
    source_currency = "USD"
    bf_fifo = BellmanFordFIFO(graph_no_cycle, source_currency)
    
    result = bf_fifo.bellman_ford(graph_no_cycle, source_currency)
    assert result is True  # Expect True as there are no negative cycles
    
    # Expected distances and parents
    expected_dist = {
        "USD": 0.0,
        "EUR": 0.5,  # USD -> EUR (0.5)
        "GBP": 1.0   # USD -> EUR (0.5) -> GBP (0.5) = 1.0
    }
    expected_parent = {
        "USD": None,
        "EUR": "USD",
        "GBP": "EUR"
    }

    # Check if all vertices in the graph are in dist and parent
    for vertex in graph_no_cycle.vertices:
        assert vertex in bf_fifo.dist, f"Vertex {vertex} not in dist"
        assert vertex in bf_fifo.parent, f"Vertex {vertex} not in parent"

    # Verify distances
    for vertex, dist_val in expected_dist.items():
        assert bf_fifo.dist[vertex] == pytest.approx(dist_val), f"Distance to {vertex} is incorrect"

    # Verify parent pointers
    for vertex, parent_val in expected_parent.items():
        assert bf_fifo.parent[vertex] == parent_val, f"Parent of {vertex} is incorrect"

    # Check that vertices not reachable from source (if any) have infinity distance
    all_vertices = graph_no_cycle.get_vertices()
    for v in all_vertices:
        if v not in expected_dist: # Should not happen with this graph fixture
            assert bf_fifo.dist[v] == float('inf')
            assert bf_fifo.parent[v] is None

def test_bellman_ford_negative_cycle(graph_negative_cycle: CurrencyGraph):
    """Test Bellman-Ford FIFO algorithm on a graph with a negative cycle."""
    source_currency = "USD"
    bf_fifo = BellmanFordFIFO(graph_negative_cycle, source_currency)

    result = bf_fifo.bellman_ford(graph_negative_cycle, source_currency)

    assert result is False  # Expect False as there is a negative cycle

def test_bellman_ford_positive_cycle(graph_positive_cycle: CurrencyGraph):
    """Test Bellman-Ford FIFO algorithm on a graph with a positive cycle (but no negative cycle)."""
    source_currency = "USD"
    bf_fifo = BellmanFordFIFO(graph_positive_cycle, source_currency)
    
    result = bf_fifo.bellman_ford(graph_positive_cycle, source_currency)

    assert result is True # Positive cycles don't make bellman_ford return False

    # Expected distances and parents. The positive cycle doesn't affect shortest path from USD
    # as long as the algorithm runs for |V|-1 iterations (or uses FIFO optimization)
    expected_dist = {
        "USD": 0.0,
        "EUR": 0.5, 
        "GBP": 1.0, 
    }
    # Parents might be tricky due to cycle, but for shortest path from USD:
    expected_parent = {
        "USD": None,
        "EUR": "USD",
        "GBP": "EUR",
    }

    for vertex in graph_positive_cycle.vertices:
        assert vertex in bf_fifo.dist, f"Vertex {vertex} not in dist"
        assert vertex in bf_fifo.parent, f"Vertex {vertex} not in parent"

    for vertex, dist_val in expected_dist.items():
         # The cycle GBP -> USD with weight 2.5 might cause issues if relaxations continue
         # indefinitely. However, bellman_ford should terminate.
         # The core idea is that d[USD] should remain 0, d[EUR] = 0.5, d[GBP] = 1.0
         # If d[USD] gets updated via GBP (e.g. 1.0 + 2.5 = 3.5), it's not shorter.
         # The parent of USD should remain None from initialization for the shortest path tree.
        assert bf_fifo.dist[vertex] == pytest.approx(dist_val), f"Distance to {vertex} is incorrect"

    # Check parents carefully for non-cycled paths from source
    assert bf_fifo.parent["USD"] == expected_parent["USD"]
    assert bf_fifo.parent["EUR"] == expected_parent["EUR"]
    assert bf_fifo.parent["GBP"] == expected_parent["GBP"]

def test_bellman_ford_zero_cycle(graph_zero_cycle: CurrencyGraph):
    """Test Bellman-Ford FIFO algorithm on a graph with a zero-weight cycle."""
    source_currency = "USD"
    bf_fifo = BellmanFordFIFO(graph_zero_cycle, source_currency)
    
    result = bf_fifo.bellman_ford(graph_zero_cycle, source_currency)

    assert result is True  # Zero-weight cycles are not negative cycles

    expected_dist = {
        "USD": 0.0,
        "EUR": 0.0, 
        "GBP": 0.0, 
    }

    for vertex in graph_zero_cycle.vertices:
        assert vertex in bf_fifo.dist, f"Vertex {vertex} not in dist"
        assert vertex in bf_fifo.parent, f"Vertex {vertex} not in parent"

    for vertex, dist_val in expected_dist.items():
        assert bf_fifo.dist[vertex] == pytest.approx(dist_val), f"Distance to {vertex} is incorrect"

    assert bf_fifo.parent["USD"] is None
    assert bf_fifo.parent["EUR"] == "USD" # From USD (0) + 0 = 0
    assert bf_fifo.parent["GBP"] == "EUR" # From EUR (0) + 0 = 0

def test_bellman_ford_disconnected_graph(graph_disconnected_component: CurrencyGraph):
    """Test Bellman-Ford FIFO on a graph with disconnected components."""
    source_currency = "USD"
    bf_fifo = BellmanFordFIFO(graph_disconnected_component, source_currency)

    result = bf_fifo.bellman_ford(graph_disconnected_component, source_currency)

    assert result is True # No negative cycle

    expected_dist = {
        "USD": 0.0,
        "EUR": 0.5,
        "CAD": float('inf'),
        "JPY": float('inf'),
        "GBP": float('inf') # Isolated node
    }
    expected_parent = {
        "USD": None,
        "EUR": "USD",
        "CAD": None,
        "JPY": None,
        "GBP": None
    }

    all_vertices = graph_disconnected_component.get_vertices()
    for vertex in all_vertices:
        assert vertex in bf_fifo.dist, f"Vertex {vertex} not in dist"
        assert vertex in bf_fifo.parent, f"Vertex {vertex} not in parent (or not initialized correctly)"
        assert bf_fifo.dist[vertex] == pytest.approx(expected_dist[vertex]), f"Distance to {vertex} is incorrect"
        assert bf_fifo.parent[vertex] == expected_parent[vertex], f"Parent of {vertex} is incorrect"

def test_bellman_ford_single_node_no_edges(graph_single_node_no_edges: CurrencyGraph):
    """Test Bellman-Ford FIFO on a graph with a single node and no edges."""
    source_currency = "USD"
    bf_fifo = BellmanFordFIFO(graph_single_node_no_edges, source_currency)
    result = bf_fifo.bellman_ford(graph_single_node_no_edges, source_currency)

    assert result is True # No negative cycles
    assert len(bf_fifo.dist) == 1
    assert bf_fifo.dist["USD"] == 0.0
    assert len(bf_fifo.parent) == 1
    assert bf_fifo.parent["USD"] is None
