from dataclasses import dataclass
from typing import Dict, Set, Tuple, List
from math import log

@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    weight: float

    def __eq__(self, other):
        if not isinstance(other, Edge):
            return NotImplemented
        return (self.source == other.source and 
                self.target == other.target)
    
    def __hash__(self):
        return hash((self.source, self.target))

class CurrencyGraph:
    def __init__(self):
        self.vertices: Set[str] = set()
        self.edges: Set[Edge] = set() 

    def add_vertex(self, vertex: str) -> None:
        """
        Add a vertex to the graph.
        """
        self.vertices.add(vertex)
    
    def add_edge(self, edge: Edge) -> None:
        """
        Add an edge to the graph.
        """
        self.edges.add(edge)
        self.add_vertex(edge.source)
        self.add_vertex(edge.target)

    def remove_edge(self, edge: Edge) -> None:
        """
        Remove an edge from the graph.
        """
        # Remove edge
        self.edges.remove(edge)
        # Check to see if the vertex at either end of the edge is disconnected (i.e. no other edges connecting to/from it)
        source_vertex_edges = tuple(filter(lambda e: e.source == edge.source or e.target == edge.source, self.edges))
        target_vertex_edges = tuple(filter(lambda e: e.target == edge.target or e.source == edge.target, self.edges))
        # If the vertex at either (or both) ends of the edge is disconnected, remove it
        if len(source_vertex_edges) == 0:
            self.remove_vertex(edge.source)
        if len(target_vertex_edges) == 0:
            self.remove_vertex(edge.target)

    def remove_vertex(self, vertex: str) -> None:
        """
        Remove a vertex from the graph.
        """
        # Remove all edges connected to the vertex
        self.edges = set(filter(lambda e: e.source != vertex and e.target != vertex, self.edges))
        # Remove the vertex
        self.vertices.remove(vertex)

    def get_vertices(self) -> Set[str]:
        """
        Get all vertices in the graph.
        """
        return self.vertices
    
    def get_edges(self) -> Set[Edge]:
        """
        Get all edges in the graph.
        """
        return self.edges

    def get_edge_weight(self, source: str, target: str) -> float:
        """
        Get the weight of an edge.
        """
        # Check if the edge exists
        filtered_edges = tuple(filter(lambda edge: edge.source == source and edge.target == target, self.edges))
        if filtered_edges:
            # Return the weight of the edge
            return filtered_edges[0].weight
        else:
            raise ValueError(f"Edge {source} -> {target} does not exist")
    
    def get_neighbors(self, vertex: str) -> Set[str]:
        """
        Get all neighbors of a vertex.
        """
        if vertex not in self.vertices:
            raise KeyError(f"Vertex {vertex} does not exist")
        neighbors = set(edge.target for edge in self.edges if edge.source == vertex)
        if len(neighbors) == 0:
            return set()
        return neighbors

    def build_from_rates(self, rates: Dict[Tuple[str, str], float]) -> None:
        """
        Build the graph from a dictionary of exchange rates.
        """
        for (source, target), rate in rates.items():
            self.add_edge(Edge(source, target, rate))

    def clear(self) -> None:
        """
        Remove everything from the graph.
        """
        self.vertices.clear()
        self.edges.clear()

    # TODO: Future feature - Add a method to expand the graph with new pairs