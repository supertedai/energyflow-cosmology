import json
import networkx as nx
from pathlib import Path
from pyvis.network import Network
import streamlit as st


# -------------------------------
# Load meta-graph
# -------------------------------
ROOT = Path(__file__).resolve().parent
GRAPH_PATH = ROOT / "meta-graph" / "meta-graph.jsonld"

def load_graph():
    with GRAPH_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


# -------------------------------
# Parse nodes and edges
# -------------------------------
def parse_graph(data):
    G = nx.DiGraph()

    nodes = data.get("@graph", [])
    for n in nodes:
        nid = n.get("@id") or n.get("id")
        name = n.get("name", "")
        layer = n.get("layer", n.get("efc:layer", "unknown"))
        ntype = n.get("@type") or n.get("type", "Node")

        G.add_node(nid, label=name, layer=layer, type=ntype)

        # parse edges
        for key, targets in n.items():
            if key in {
                "dependsOn", "produces", "stabilises", "amplifies",
                "emergesFrom", "implementedBy", "documentedIn",
                "efc:dependsOn", "efc:produces", "efc:stabilises",
                "efc:amplifies", "efc:emergesFrom",
                "efc:implementedBy", "efc:documentedIn"
            }:
                if isinstance(targets, str):
                    targets = [targets]
                for tgt in targets:
                    G.add_edge(nid, tgt, relation=key)

    return G


# -------------------------------
# Generate interactive PyVis graph
# -------------------------------
def generate_pyvis(G):
    net = Network(height="720px", width="100%", directed=True)
    net.toggle_physics(True)

    for node, attrs in G.nodes(data=True):
        label = attrs.get("label", node)
        layer = attrs.get("layer", "meta")
        color = {
            "cognition": "#FFB347",
            "symbiosis": "#BEB8EB",
            "meta": "#A3D5FF",
            "meta_process": "#FFD1DC",
            "methodology": "#C3FDB8",
            "theory": "#FFF380"
        }.get(layer, "#DDDDDD")

        net.add_node(node, label=label, color=color)

    for src, tgt, attrs in G.edges(data=True):
        rel = attrs.get("relation", "")
        net.add_edge(src, tgt, title=rel, label=rel)

    outpath = ROOT / "meta-graph" / "meta_graph_vis.html"
    net.save_graph(str(outpath))

    return outpath


# -------------------------------
# STREAMLIT UI
# -------------------------------
def main():
    st.title("EFC Meta-Knowledge Graph Dashboard")
    st.write("Visualisation of the metascope meta-architecture.")

    data = load_graph()
    G = parse_graph(data)

    st.subheader("1. Nodes")
    st.write(f"Total nodes: {len(G.nodes)}")
    st.dataframe([
        {"id": n, **G.nodes[n]} for n in G.nodes()
    ])

    st.subheader("2. Edges")
    st.write(f"Total edges: {len(G.edges)}")
    st.dataframe([
        {"source": u, "target": v, "relation": G.edges[u, v].get("relation")}
        for u, v in G.edges()
    ])

    st.subheader("3. Graph Visualisation")
    html_path = generate_pyvis(G)
    st.write("Interactive graph saved as:")
    st.code(str(html_path))
    st.write("Open file directly in browser after running Streamlit.")


if __name__ == "__main__":
    main()
