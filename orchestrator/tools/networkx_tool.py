from typing import Any
import numpy as np
from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result


class NetworkXTool(SimulationTool):
    name = "NetworkX"
    key = "networkx"
    layer = "engineering"

    SIMULATION_TYPES = {"graph_analysis", "shortest_path", "centrality", "community_detection", "max_flow"}

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        sim_type = params.get("simulation_type", "graph_analysis")
        if sim_type not in self.SIMULATION_TYPES:
            raise ValueError(f"Unknown simulation_type: {sim_type}. Supported: {self.SIMULATION_TYPES}")

        params.setdefault("simulation_type", sim_type)
        params.setdefault("directed", False)
        return params

    def _build_graph(self, params):
        import networkx as nx

        directed = params.get("directed", False)
        G = nx.DiGraph() if directed else nx.Graph()

        nodes = params.get("nodes", [])
        edges = params.get("edges", [])

        # Handle special built-in graphs
        if nodes == "karate_club":
            return nx.karate_club_graph()
        if nodes == "petersen":
            return nx.petersen_graph()

        # Add nodes
        for n in nodes:
            if isinstance(n, dict):
                G.add_node(n["id"], label=n.get("label", str(n["id"])))
            else:
                G.add_node(n)

        # Add edges
        for e in edges:
            if isinstance(e, dict):
                G.add_edge(e["source"], e["target"], weight=e.get("weight", 1))
            elif isinstance(e, (list, tuple)) and len(e) >= 2:
                w = e[2] if len(e) > 2 else 1
                G.add_edge(e[0], e[1], weight=w)

        return G

    def _compute_layout(self, G):
        import networkx as nx
        pos = nx.spring_layout(G, seed=42)
        return {str(k): [float(v[0]), float(v[1])] for k, v in pos.items()}

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        params = self.validate_params(params)
        sim_type = params["simulation_type"]

        if sim_type == "graph_analysis":
            return self._run_graph_analysis(params)
        elif sim_type == "shortest_path":
            return self._run_shortest_path(params)
        elif sim_type == "centrality":
            return self._run_centrality(params)
        elif sim_type == "community_detection":
            return self._run_community_detection(params)
        elif sim_type == "max_flow":
            return self._run_max_flow(params)

    def _run_graph_analysis(self, params):
        import networkx as nx

        G = self._build_graph(params)
        layout = self._compute_layout(G)

        n_nodes = G.number_of_nodes()
        n_edges = G.number_of_edges()
        density = float(nx.density(G))

        is_connected = nx.is_connected(G) if not G.is_directed() else nx.is_weakly_connected(G)
        components = nx.number_connected_components(G) if not G.is_directed() else nx.number_weakly_connected_components(G)

        diameter = None
        if is_connected and not G.is_directed():
            try:
                diameter = int(nx.diameter(G))
            except Exception:
                pass

        avg_clustering = float(nx.average_clustering(G)) if not G.is_directed() else 0.0

        # Degree distribution
        degrees = [d for _, d in G.degree()]
        unique_degrees = sorted(set(degrees))
        degree_count = [degrees.count(d) for d in unique_degrees]

        return {
            "tool": "networkx",
            "simulation_type": "graph_analysis",
            "n_nodes": n_nodes,
            "n_edges": n_edges,
            "density": density,
            "diameter": diameter,
            "avg_clustering": avg_clustering,
            "is_connected": is_connected,
            "components": components,
            "degree_distribution": {"degree": unique_degrees, "count": degree_count},
            "layout": layout,
            "nodes": list(G.nodes()),
            "edges": [[int(u), int(v)] for u, v in G.edges()],
        }

    def _run_shortest_path(self, params):
        import networkx as nx

        G = self._build_graph(params)
        source = params.get("source_node", list(G.nodes())[0])
        target = params.get("target_node", list(G.nodes())[-1])
        algorithm = params.get("algorithm", "dijkstra")

        if algorithm == "bellman_ford":
            path = nx.bellman_ford_path(G, source, target, weight="weight")
            path_length = float(nx.bellman_ford_path_length(G, source, target, weight="weight"))
        else:
            path = nx.dijkstra_path(G, source, target, weight="weight")
            path_length = float(nx.dijkstra_path_length(G, source, target, weight="weight"))

        # All shortest distances from source
        all_distances = dict(nx.single_source_dijkstra_path_length(G, source, weight="weight"))
        all_distances = {str(k): float(v) for k, v in all_distances.items()}

        layout = self._compute_layout(G)

        return {
            "tool": "networkx",
            "simulation_type": "shortest_path",
            "path": [int(n) if isinstance(n, (int, np.integer)) else n for n in path],
            "path_length": path_length,
            "all_distances": all_distances,
            "layout": layout,
            "nodes": list(G.nodes()),
            "edges": [[u, v] for u, v in G.edges()],
        }

    def _run_centrality(self, params):
        import networkx as nx

        G = self._build_graph(params)
        metric = params.get("metric", "betweenness")

        if metric == "degree":
            scores = nx.degree_centrality(G)
        elif metric == "betweenness":
            scores = nx.betweenness_centrality(G, weight="weight")
        elif metric == "closeness":
            scores = nx.closeness_centrality(G)
        elif metric == "eigenvector":
            scores = nx.eigenvector_centrality(G, max_iter=1000)
        elif metric == "pagerank":
            scores = nx.pagerank(G)
        else:
            scores = nx.degree_centrality(G)

        scores = {str(k): float(v) for k, v in scores.items()}
        top_nodes = sorted(scores, key=scores.get, reverse=True)[:10]
        layout = self._compute_layout(G)

        return {
            "tool": "networkx",
            "simulation_type": "centrality",
            "metric": metric,
            "scores": scores,
            "top_nodes": top_nodes,
            "layout": layout,
            "nodes": list(G.nodes()),
            "edges": [[u, v] for u, v in G.edges()],
        }

    def _run_community_detection(self, params):
        import networkx as nx

        G = self._build_graph(params)
        algorithm = params.get("algorithm", "louvain")

        if algorithm == "louvain":
            communities_set = nx.community.louvain_communities(G, seed=42)
        elif algorithm == "label_propagation":
            communities_set = list(nx.community.label_propagation_communities(G))
        elif algorithm == "girvan_newman":
            comp = nx.community.girvan_newman(G)
            communities_set = next(comp)
        else:
            communities_set = nx.community.louvain_communities(G, seed=42)

        communities = [sorted([int(n) if isinstance(n, (int, np.integer)) else n for n in c])
                       for c in communities_set]

        modularity = float(nx.community.modularity(G, communities_set))
        layout = self._compute_layout(G)

        return {
            "tool": "networkx",
            "simulation_type": "community_detection",
            "algorithm": algorithm,
            "communities": communities,
            "modularity": modularity,
            "n_communities": len(communities),
            "layout": layout,
            "nodes": list(G.nodes()),
            "edges": [[u, v] for u, v in G.edges()],
        }

    def _run_max_flow(self, params):
        import networkx as nx

        G = self._build_graph(params)
        if not G.is_directed():
            G = G.to_directed()

        source = params.get("source_node", list(G.nodes())[0])
        sink = params.get("sink_node", list(G.nodes())[-1])

        flow_value, flow_dict = nx.maximum_flow(G, source, sink, capacity="weight")

        # Convert flow_dict to serializable format
        flow_serializable = {}
        for u, targets in flow_dict.items():
            flow_serializable[str(u)] = {str(v): float(f) for v, f in targets.items()}

        return {
            "tool": "networkx",
            "simulation_type": "max_flow",
            "max_flow_value": float(flow_value),
            "flow_dict": flow_serializable,
            "source_node": source,
            "sink_node": sink,
        }

    def get_default_params(self) -> dict[str, Any]:
        return {
            "simulation_type": "community_detection",
            "nodes": "karate_club",
            "algorithm": "louvain",
        }


@celery_app.task(name="tools.networkx_tool.run_networkx", bind=True)
def run_networkx(self, params: dict, project: str = "_default",
                 label: str | None = None) -> dict:
    tool = NetworkXTool()

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting NetworkX analysis"})

    try:
        sim_type = params.get("simulation_type", "graph_analysis")
        self.update_state(state="PROGRESS", meta={"progress": 0.1, "message": f"Running {sim_type}"})
        result = tool.run(params)
    except Exception as e:
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    save_result(self.request.id, "networkx", result, project, label)

    return result
