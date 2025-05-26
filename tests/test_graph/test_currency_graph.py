import pytest
from math import log
from graph.currency_graph import CurrencyGraph, Edge

@pytest.fixture
def empty_graph():
    return CurrencyGraph()

@pytest.fixture
def sample_rates():
    return {
        ("USD", "EUR"): 0.92,
        ("EUR", "USD"): 1/0.92,
        ("USD", "GBP"): 0.79,
        ("GBP", "USD"): 1/0.79,
        ("EUR", "GBP"): 0.79/0.92,
        ("GBP", "EUR"): 0.92/0.79
    }

def test_edge_creation():
    """Test that Edge objects are created correctly"""
    edge = Edge("USD", "EUR", 0.92)
    assert edge.source == "USD"
    assert edge.target == "EUR"
    assert edge.weight == pytest.approx(0.92)

def create_existing_edge_changes_weight(empty_graph):
    """Test that creating an edge with the same source and target currencies changes the weight"""
    empty_graph.add_edge(Edge("USD", "EUR", 0.92))
    empty_graph.add_edge(Edge("USD", "EUR", 0.93))
    assert len(empty_graph.edges) == 1
    assert empty_graph.edges[0].weight == pytest.approx(0.93)

def test_empty_graph_creation(empty_graph):
    """Test that a new graph is created empty"""
    assert len(empty_graph.vertices) == 0
    assert len(empty_graph.edges) == 0

def test_add_single_vertex(empty_graph):
    """Test adding a single vertex"""
    empty_graph.add_vertex("USD")
    assert "USD" in empty_graph.vertices
    assert len(empty_graph.vertices) == 1

def test_add_duplicate_vertex(empty_graph):
    """Test that adding a duplicate vertex doesn't create duplicates"""
    empty_graph.add_vertex("USD")
    empty_graph.add_vertex("USD")
    assert len(empty_graph.vertices) == 1

def test_add_edge(empty_graph):
    """Test adding a single edge"""
    edge = Edge("USD", "EUR", 0.92)
    empty_graph.add_edge(edge)
    assert edge in empty_graph.edges
    assert "USD" in empty_graph.vertices
    assert "EUR" in empty_graph.vertices

def test_add_edge_with_logarithmic_weight(empty_graph):
    """Test adding an edge with a logarithmic weight"""
    edge = Edge("USD", "EUR", -log(0.92))
    empty_graph.add_edge(edge)
    assert edge in empty_graph.edges
    assert "USD" in empty_graph.vertices
    assert "EUR" in empty_graph.vertices

def test_add_edge_with_negative_weight(empty_graph):
    """Test adding an edge with a negative weight"""
    edge = Edge("USD", "EUR", -1.0)
    empty_graph.add_edge(edge)
    assert edge in empty_graph.edges
    assert "USD" in empty_graph.vertices
    assert "EUR" in empty_graph.vertices

def test_add_edge_with_zero_weight(empty_graph):
    """Test adding an edge with a zero weight"""
    edge = Edge("USD", "EUR", 0.0)
    empty_graph.add_edge(edge)
    assert edge in empty_graph.edges
    assert "USD" in empty_graph.vertices
    assert "EUR" in empty_graph.vertices

def test_add_edge_with_positive_weight(empty_graph):
    """Test adding an edge with a positive weight"""
    edge = Edge("USD", "EUR", 1.0)
    empty_graph.add_edge(edge)
    assert edge in empty_graph.edges
    assert "USD" in empty_graph.vertices
    assert "EUR" in empty_graph.vertices

def test_add_edge_with_large_weight(empty_graph):
    """Test adding an edge with a large weight"""
    edge = Edge("USD", "EUR", 1e10)
    empty_graph.add_edge(edge)
    assert edge in empty_graph.edges
    assert "USD" in empty_graph.vertices
    assert "EUR" in empty_graph.vertices

def test_add_edge_with_small_weight(empty_graph):
    """Test adding an edge with a small weight"""
    edge = Edge("USD", "EUR", 1e-10)
    empty_graph.add_edge(edge)
    assert edge in empty_graph.edges
    assert "USD" in empty_graph.vertices
    assert "EUR" in empty_graph.vertices

def test_add_edge_with_integer_weight(empty_graph):
    """Test adding an edge with an integer weight"""
    edge = Edge("USD", "EUR", 1)
    empty_graph.add_edge(edge)
    assert edge in empty_graph.edges
    assert "USD" in empty_graph.vertices
    assert "EUR" in empty_graph.vertices

def test_add_duplicate_edge(empty_graph):
    """Test that adding duplicate edges doesn't create duplicates"""
    edge1 = Edge("USD", "EUR", 0.92)
    edge2 = Edge("USD", "EUR", 0.92)
    empty_graph.add_edge(edge1)
    empty_graph.add_edge(edge2)
    assert len(empty_graph.edges) == 1

def test_build_from_rates(empty_graph, sample_rates):
    """Test building graph from dictionary of rates"""
    empty_graph.build_from_rates(sample_rates)
    
    # Check vertices
    expected_vertices = {"USD", "EUR", "GBP"}
    assert empty_graph.vertices == expected_vertices
    
    # Check number of edges
    assert len(empty_graph.edges) == len(sample_rates)
    
    # Check specific edge exists with correct weight
    usd_eur_edge = Edge("USD", "EUR", 0.92)
    assert any(edge == usd_eur_edge for edge in empty_graph.edges)

def test_get_edge_weight(empty_graph):
    """Test retrieving weight of an edge"""
    edge = Edge("USD", "EUR", 0.92)
    empty_graph.add_edge(edge)
    weight = empty_graph.get_edge_weight("USD", "EUR")
    assert weight == pytest.approx(0.92)

def test_get_nonexistent_edge_weight_raises_error(empty_graph):
    """Test that getting weight of a nonexistent edge raises an error"""
    with pytest.raises(ValueError):
        empty_graph.get_edge_weight("USD", "EUR")

def test_get_neighbors(empty_graph, sample_rates):
    """Test getting neighbors of a vertex"""
    empty_graph.build_from_rates(sample_rates)
    neighbors = empty_graph.get_neighbors("USD")
    assert set(neighbors) == {"EUR", "GBP"}

def test_get_neighbors_for_nonexistent_vertex_raises_error(empty_graph):
    """Test that getting neighbors of a nonexistent vertex raises an error"""
    with pytest.raises(KeyError):
        empty_graph.get_neighbors("USD")

def test_remove_vertex(empty_graph, sample_rates):
    """Test removing a vertex and its associated edges"""
    empty_graph.build_from_rates(sample_rates)
    empty_graph.remove_vertex("USD")
    assert "USD" not in empty_graph.vertices
    assert all(edge.source != "USD" and edge.target != "USD" for edge in empty_graph.edges)

def test_remove_edge(empty_graph):
    """Test removing an edge"""
    edge = Edge("USD", "EUR", 0.92)
    empty_graph.add_edge(edge)
    assert edge in empty_graph.edges
    empty_graph.remove_edge(edge)
    assert edge not in empty_graph.edges

def test_remove_edge_removes_vertex_if_necessary(empty_graph):
    """Test that removing an edge removes a vertex if it has no other edges"""
    empty_graph.add_edge(Edge("USD", "EUR", 0.92))
    empty_graph.add_edge(Edge("EUR", "GBP", 0.79))
    empty_graph.remove_edge(Edge("EUR", "GBP", 0.79))
    assert "GBP" not in empty_graph.vertices
    assert "EUR" in empty_graph.vertices
    assert "USD" in empty_graph.vertices

def test_remove_vertex_removes_associated_edges(empty_graph):
    """Test that removing a vertex removes all edges associated with it"""
    empty_graph.add_edge(Edge("USD", "EUR", 0.92))
    empty_graph.add_edge(Edge("EUR", "GBP", 0.79))
    empty_graph.remove_vertex("GBP")
    assert Edge("EUR", "GBP", 0.79) not in empty_graph.edges
    assert Edge("USD", "EUR", 0.92) in empty_graph.edges

def test_clear_graph(empty_graph, sample_rates):
    """Test clearing all vertices and edges from graph"""
    empty_graph.build_from_rates(sample_rates)
    empty_graph.clear()
    assert len(empty_graph.vertices) == 0
    assert len(empty_graph.edges) == 0 