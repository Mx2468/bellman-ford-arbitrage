from collections import deque
from typing import Dict, Tuple
from graph.currency_graph import CurrencyGraph


class BellmanFord:
    def __init__(self, graph: CurrencyGraph, source: str):
        self.dist: Dict[Tuple[str, str], float] = {}
        self.parent: Dict[str, str] = {}
        self.weights: Dict[Tuple[str, str], float] = {}
        for edge in graph.edges:
            self.weights[(edge.source, edge.target)] = edge.weight

    def initialise(self, graph: CurrencyGraph, source: str):
        for vertex in graph.vertices:
            self.dist[vertex] = float('inf')
            self.parent[vertex] = None
        self.dist[source] = 0.0

    def relax_operation(self, source: str, target: str) -> None:
        if self.dist[target] > self.dist[source] + self.weights[(source, target)]:
            self.dist[target] = self.dist[source] + self.weights[(source, target)]
            self.parent[target] = source

    def bellman_ford(self, graph: CurrencyGraph, source: str) -> bool:
        self.initialise(graph, source)

        n = len(graph.vertices)
        for _ in range(1, n):
            for edge in graph.edges:
                self.relax_operation(edge.source, edge.target)

        for edge in graph.edges:
            if self.dist[edge.target] > (self.dist[edge.source] + self.weights[(edge.source, edge.target)]):
                return False
        return True


class BellmanFordFIFO:
    def __init__(self, graph: CurrencyGraph, source: str):
        self.dist: Dict[Tuple[str, str], float] = {}
        self.parent: Dict[str, str] = {}
        self.active_vertices: deque[str] = deque()
        self.weights: Dict[Tuple[str, str], float] = {}
        for edge in graph.edges:
            self.weights[(edge.source, edge.target)] = edge.weight
    
    def initialise(self, graph: CurrencyGraph, source: str):
        for vertex in graph.vertices:
            self.dist[vertex] = float('inf')
            self.parent[vertex] = None
        self.dist[source] = 0.0

    def relax_operation(self, source: str, target: str) -> None:
        if self.dist[target] > self.dist[source] + self.weights[(source, target)]:
            self.dist[target] = self.dist[source] + self.weights[(source, target)]
            self.parent[target] = source
            if target not in self.active_vertices:
                self.active_vertices.append(target)

    def detect_parent_node_cycle(self, graph: CurrencyGraph, current_vertex: str) -> bool:
        visited_nodes = set()
        while self.parent[current_vertex] not in visited_nodes:
            parent = self.parent[current_vertex]
            if parent is None:
                return False # We have reached the source node, and there is no negative cycle
            visited_nodes.add(parent)
            current_vertex = parent
        return True

    def bellman_ford(self, graph: CurrencyGraph, source: str) -> bool:
        self.initialise(graph, source)
        self.active_vertices = deque(graph.vertices)

        while self.active_vertices:
            u = self.active_vertices.popleft()
            for v in graph.get_neighbors(u):
                self.relax_operation(u, v)
                # If parents form a cycle, then there is a negative cycle
                if self.detect_parent_node_cycle(graph, v):
                    return False

        return True


"""
Ideas for speed optimisations:
Try to decrease the number of iterations of loop 1:
    If no effective relax operation in the current iteration, then terminate: the shortest-path weights are already computed.
    Check periodically (at the end of each iteration of loop 1?) if the parent pointers form a cycle. If they do, then terminate and return false: there is a negative cycle reachable from s.

Try to decrease the running time of one iteration of loop 1 - consider only edges which may give effective relax operations.
    We say a vertex u is active, if the edges outgoing from u have not been relaxed since the last time d[u] has been decreased.
    Perform RELAX only on edges outgoing from active vertices.
    Store active vertices in the Queue data structure.
    (If we change d[u], then only relax the edges outgoing from u.)
"""