"""
NetworkX Repository Knowledge Graph for History-RAG.
Implements Section 33 Enhancement #1:
Explicit multi-relational graph: Issue -> PR -> Commit -> File -> Test -> Component.
Provides multi-hop path tracing, graph centrality scoring, and structural test ranking.
"""
import json
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
import networkx as nx

from app.ingestion.sqlite_store import SQLiteMetadataStore

logger = logging.getLogger(__name__)


class RepositoryKnowledgeGraph:
    def __init__(self, sqlite_store: Optional[SQLiteMetadataStore] = None):
        self.sqlite = sqlite_store or SQLiteMetadataStore()
        self.graph = nx.MultiDiGraph()
        self.repository_id: Optional[str] = None
        self.max_timestamp: Optional[str] = None

    def build_graph(
        self,
        repository_id: str,
        max_timestamp: Optional[str] = None,
        excluded_commit_shas: Optional[Set[str]] = None,
        excluded_issue_ids: Optional[Set[str]] = None,
        excluded_pr_ids: Optional[Set[str]] = None,
        excluded_test_paths: Optional[Set[str]] = None,
    ) -> nx.MultiDiGraph:
        """
        Builds the repository multigraph from SQLite metadata with strict temporal leakage filtering.
        """
        self.repository_id = repository_id
        self.max_timestamp = max_timestamp
        self.graph.clear()

        excluded_commits = excluded_commit_shas or set()
        excluded_issues = excluded_issue_ids or set()
        excluded_prs = excluded_pr_ids or set()
        excluded_tests = excluded_test_paths or set()

        # 1. Fetch documents up to max_timestamp
        docs = self.sqlite.query_documents(
            repository_id=repository_id,
            max_timestamp=max_timestamp,
            limit=2000
        )

        seen_components: Set[str] = set()

        for doc in docs:
            comp = doc.component or "core"
            comp_node = f"comp:{comp}"
            if comp not in seen_components:
                self.graph.add_node(
                    comp_node,
                    node_type="component",
                    label=comp,
                    name=comp
                )
                seen_components.add(comp)

            # Node: Code file
            if doc.type.value == "code" and doc.path:
                file_node = f"file:{doc.path}"
                self.graph.add_node(
                    file_node,
                    node_type="file",
                    label=doc.path.split("/")[-1],
                    path=doc.path,
                    component=comp
                )
                self.graph.add_edge(file_node, comp_node, relation="BELONGS_TO", weight=1.0)

            # Node: Test file
            elif doc.type.value == "test" and doc.path:
                if doc.path in excluded_tests:
                    continue
                test_node = f"test:{doc.path}"
                self.graph.add_node(
                    test_node,
                    node_type="test",
                    label=doc.path.split("/")[-1],
                    path=doc.path,
                    component=comp
                )
                self.graph.add_edge(test_node, comp_node, relation="TESTS", weight=1.0)

            # Node: Commit
            elif doc.type.value == "commit" and doc.commit_sha:
                if doc.commit_sha in excluded_commits:
                    continue
                sha = doc.commit_sha
                short_sha = sha[:8]
                commit_node = f"commit:{short_sha}"
                self.graph.add_node(
                    commit_node,
                    node_type="commit",
                    label=f"Commit {short_sha}",
                    sha=sha,
                    title=doc.title,
                    timestamp=doc.event_timestamp,
                    component=comp
                )
                self.graph.add_edge(commit_node, comp_node, relation="TOUCHES", weight=1.0)

                # Connect commit to changed files if present in metadata
                files_changed = doc.metadata.get("files_changed", [])
                for f in files_changed:
                    f_node = f"test:{f}" if "test" in f.lower() else f"file:{f}"
                    if not self.graph.has_node(f_node):
                        node_t = "test" if "test" in f.lower() else "file"
                        self.graph.add_node(f_node, node_type=node_t, label=f.split("/")[-1], path=f, component=comp)
                    rel = "MODIFIES_TEST" if "test" in f.lower() else "MODIFIES"
                    self.graph.add_edge(commit_node, f_node, relation=rel, weight=1.0)

            # Node: Issue
            elif doc.type.value == "issue" and doc.issue_id:
                if str(doc.issue_id) in excluded_issues:
                    continue
                issue_node = f"issue:#{doc.issue_id}"
                self.graph.add_node(
                    issue_node,
                    node_type="issue",
                    label=f"Issue #{doc.issue_id}",
                    issue_id=doc.issue_id,
                    title=doc.title,
                    timestamp=doc.event_timestamp,
                    component=comp
                )
                self.graph.add_edge(issue_node, comp_node, relation="DISCUSSES", weight=1.0)

                # Link Issue to PRs
                linked_prs = doc.metadata.get("linked_prs", [])
                for pr_id in linked_prs:
                    pr_node = f"pr:#{pr_id}"
                    self.graph.add_edge(issue_node, pr_node, relation="RESOLVED_BY", weight=1.0)

            # Node: Pull Request
            elif doc.type.value == "pr" and doc.pr_id:
                if str(doc.pr_id) in excluded_prs:
                    continue
                pr_node = f"pr:#{doc.pr_id}"
                self.graph.add_node(
                    pr_node,
                    node_type="pr",
                    label=f"PR #{doc.pr_id}",
                    pr_id=doc.pr_id,
                    title=doc.title,
                    timestamp=doc.event_timestamp,
                    component=comp
                )
                self.graph.add_edge(pr_node, comp_node, relation="PROPOSES_CHANGE", weight=1.0)

                linked_issues = doc.metadata.get("linked_issues", [])
                for i_id in linked_issues:
                    i_node = f"issue:#{i_id}"
                    self.graph.add_edge(pr_node, i_node, relation="FIXES", weight=1.0)

        # 2. Add Component Co-Change Edges from SQLite co_changes
        for comp in seen_components:
            co_counts = self.sqlite.get_co_change_counts(
                repository_id=repository_id,
                source_component=comp,
                max_timestamp=max_timestamp
            )
            for peer, cnt in co_counts.items():
                if peer in seen_components:
                    self.graph.add_edge(
                        f"comp:{comp}",
                        f"comp:{peer}",
                        relation="CO_CHANGED_WITH",
                        weight=min(1.0, cnt * 0.1),
                        count=cnt
                    )

        # 3. Add Component Import Dependencies from SQLite dependencies
        for comp in seen_components:
            deps = self.sqlite.get_dependencies_for_component(repository_id, comp)
            for dep in deps:
                tgt = dep.get("target_component")
                if tgt and tgt in seen_components and tgt != comp:
                    self.graph.add_edge(
                        f"comp:{comp}",
                        f"comp:{tgt}",
                        relation="DEPENDS_ON",
                        import_statement=dep.get("import_statement", ""),
                        weight=1.0
                    )

        logger.info(
            f"Built Knowledge Graph for [{repository_id}]: "
            f"{self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges."
        )
        return self.graph

    def find_impact_paths(
        self,
        source_components: List[str],
        target_components: Optional[List[str]] = None,
        max_hops: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Finds explicit multi-hop causal paths between modified source components and other components/tests.
        Example path: comp:dcim -> CO_CHANGED_WITH -> comp:ipam -> TESTS -> test:test_ipam.py
        """
        if self.graph.number_of_nodes() == 0:
            return []

        undirected = self.graph.to_undirected(as_view=True)
        paths_found = []

        sources = [f"comp:{c}" for c in source_components if self.graph.has_node(f"comp:{c}")]
        if not sources:
            return []

        targets = []
        if target_components:
            targets = [f"comp:{c}" for c in target_components if self.graph.has_node(f"comp:{c}")]
        else:
            # Look for all test nodes and connected component nodes
            targets = [
                n for n, data in self.graph.nodes(data=True)
                if data.get("node_type") in ("test", "component") and n not in sources
            ]

        for s in sources:
            if len(paths_found) >= 15:
                break
            for t in targets[:25]:
                if s == t:
                    continue
                try:
                    p = nx.shortest_path(undirected, source=s, target=t)
                    if len(p) - 1 <= max_hops:
                        # Reconstruct edge labels
                        path_steps = []
                        for idx in range(len(p) - 1):
                            u, v = p[idx], p[idx + 1]
                            # Get edge data
                            edge_data = self.graph.get_edge_data(u, v) or self.graph.get_edge_data(v, u) or {}
                            rel = "CONNECTED_TO"
                            if edge_data:
                                first_key = list(edge_data.keys())[0]
                                rel = edge_data[first_key].get("relation", "CONNECTED_TO")
                            path_steps.append({
                                "from": u,
                                "to": v,
                                "relation": rel
                            })
                        paths_found.append({
                            "source": s,
                            "target": t,
                            "hops": len(p) - 1,
                            "path_nodes": p,
                            "steps": path_steps
                        })
                        if len(paths_found) >= 15:
                            break
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    continue

        return paths_found

    def rank_tests_by_graph_proximity(
        self,
        affected_components: List[str],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Ranks existing regression tests using graph shortest path distances from affected components.
        Tests directly connected have hop distance 1 (highest score); multi-hop tests have decaying scores.
        """
        if self.graph.number_of_nodes() == 0:
            return []

        undirected = self.graph.to_undirected(as_view=True)
        test_scores = {}

        source_nodes = [f"comp:{c}" for c in affected_components if self.graph.has_node(f"comp:{c}")]
        if not source_nodes:
            # Fallback to any node matching component name
            source_nodes = [
                n for n, d in self.graph.nodes(data=True)
                if any(c.lower() in n.lower() for c in affected_components)
            ]

        test_nodes = [
            (n, d) for n, d in self.graph.nodes(data=True)
            if d.get("node_type") == "test"
        ]

        for t_node, t_data in test_nodes:
            path = t_data.get("path", t_node.replace("test:", ""))
            min_hops = 999
            best_source = None

            for s_node in source_nodes:
                try:
                    d = nx.shortest_path_length(undirected, source=s_node, target=t_node)
                    if d < min_hops:
                        min_hops = d
                        best_source = s_node
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    continue

            if min_hops < 999:
                # Graph proximity score: 1.0 for 1 hop, 0.7 for 2 hops, 0.4 for 3 hops, etc.
                proximity_score = max(0.1, 1.0 / min_hops)
                test_scores[path] = {
                    "test_file": path,
                    "graph_score": round(proximity_score, 4),
                    "hops": min_hops,
                    "connected_via": best_source,
                    "reasons": [f"Graph connectivity distance: {min_hops} hop(s) from {best_source}"]
                }

        sorted_tests = sorted(test_scores.values(), key=lambda x: x["graph_score"], reverse=True)
        return sorted_tests[:top_k]

    def compute_personalized_pagerank(
        self,
        seed_components: List[str]
    ) -> Dict[str, float]:
        """
        Computes Personalized PageRank (PPR) seeded with the proposed change components
        to identify structurally coupled components across the entire repository.
        """
        if self.graph.number_of_nodes() == 0:
            return {}

        personalization = {}
        for n in self.graph.nodes():
            personalization[n] = 0.0

        seeds = [f"comp:{c}" for c in seed_components if self.graph.has_node(f"comp:{c}")]
        if not seeds:
            return {}

        for s in seeds:
            personalization[s] = 1.0 / len(seeds)

        try:
            ppr = nx.pagerank(self.graph, alpha=0.85, personalization=personalization, max_iter=100)
            # Filter and normalize component scores
            comp_scores = {}
            for n, score in ppr.items():
                if n.startswith("comp:"):
                    c_name = n.replace("comp:", "")
                    comp_scores[c_name] = round(score, 4)
            return comp_scores
        except Exception as e:
            logger.warning(f"PageRank computation fallback: {e}")
            return {c: 0.5 for c in seed_components}

    def get_subgraph_data_for_ui(
        self,
        components: Optional[List[str]] = None,
        max_nodes: int = 50
    ) -> Dict[str, Any]:
        """
        Exports a clean node-link dictionary (nodes + edges) for interactive UI rendering.
        """
        if self.graph.number_of_nodes() == 0:
            return {"nodes": [], "edges": []}

        sub_nodes = set()
        if components:
            for c in components:
                c_node = f"comp:{c}"
                if self.graph.has_node(c_node):
                    sub_nodes.add(c_node)
                    # Add 1-hop neighbors
                    sub_nodes.update(list(self.graph.neighbors(c_node))[:10])
                    # Add predecessors
                    sub_nodes.update(list(self.graph.predecessors(c_node))[:10])

        if not sub_nodes:
            sub_nodes = set(list(self.graph.nodes())[:max_nodes])
        else:
            sub_nodes = set(list(sub_nodes)[:max_nodes])

        subgraph = self.graph.subgraph(sub_nodes)

        nodes_list = []
        for n in subgraph.nodes():
            d = self.graph.nodes[n]
            node_type = d.get("node_type", "unknown")
            color_map = {
                "component": "#4CAF50",
                "file": "#2196F3",
                "test": "#FF9800",
                "commit": "#9C27B0",
                "issue": "#E91E63",
                "pr": "#00BCD4"
            }
            nodes_list.append({
                "id": n,
                "label": d.get("label", n),
                "type": node_type,
                "color": color_map.get(node_type, "#9E9E9E")
            })

        edges_list = []
        for u, v, k, d in subgraph.edges(data=True, keys=True):
            edges_list.append({
                "from": u,
                "to": v,
                "relation": d.get("relation", "LINKED")
            })

        return {
            "nodes": nodes_list,
            "edges": edges_list,
            "total_graph_nodes": self.graph.number_of_nodes(),
            "total_graph_edges": self.graph.number_of_edges()
        }
