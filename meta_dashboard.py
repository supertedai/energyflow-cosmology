import json
from pathlib import Path

import networkx as nx
from pyvis.network import Network
import streamlit as st
import streamlit.components.v1 as components


ROOT = Path(__file__).resolve().parent
GRAPH_PATH = ROOT / "meta-graph" / "meta-graph.jsonld"

# Map node IDs to repo-relative paths for clickable links
NODE_PATHS = {
    "efc:MetaReflectiveProtocolDoc": "meta/meta-reflective-protocol.md",
    "efc:MetaArchitectureDoc": "meta/meta-architecture-spec.md",
    "efc:CognitiveSignatureDoc": "cognition/cognitive-signature.md",
    "efc:CoFieldSimulatorModule": "src/efc/meta/cofield_simulator.py",
    "efc:EFC_MasterSpec": "theory/formal/efc_master.tex",
    "efc:CoFieldSimulator": "meta-graph/meta-graph.jsonld",
}

GITHUB_BASE = "https://github.com/supertedai/energyflow-cosmology/blob/main/"


def load_graph_json() -> dict:
    with GRAPH_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_graph(data: dict) -> nx.DiGraph:
    G = nx.DiGraph()
    nodes = data.get("@graph", [])

    for n in nodes:
        nid = n.get("@id") or n.get("id")
        if not nid:
            continue

        name = n.get("name") or n.get("schema:name") or nid
        layer = n.get("layer") or n.get("efc:layer") or "unknown"
        ntype = n.get("@type") or n.get("type") or "Node"
        desc = n.get("description", "")

        G.add_node(
            nid,
            label=name,
            layer=layer,
            type=ntype,
            description=desc,
        )

        for key, targets in n.items():
            if key in {
                "dependsOn", "produces", "stabilises", "amplifies",
                "emergesFrom", "implementedBy", "documentedIn",
                "efc:dependsOn", "efc:produces", "efc:stabilises",
                "efc:amplifies", "efc:emergesFrom",
                "efc:implementedBy", "efc:documentedIn",
            }:
                if isinstance(targets, str):
                    targets = [targets]
                for tgt in targets:
                    G.add_edge(nid, tgt, relation=key)

    return G


def filter_graph(
    G: nx.DiGraph,
    layers: list[str] | None,
    relations: list[str] | None,
) -> nx.DiGraph:
    if not layers and not relations:
        return G.copy()

    H = nx.DiGraph()

    for u, v, attrs in G.edges(data=True):
        rel = attrs.get("relation")
        u_layer = G.nodes[u].get("layer")
        v_layer = G.nodes[v].get("layer")

        if layers and (u_layer not in layers and v_layer not in layers):
            continue

        if relations and rel not in relations:
            continue

        # add edge + nodes
        H.add_node(u, **G.nodes[u])
        H.add_node(v, **G.nodes[v])
        H.add_edge(u, v, **attrs)

    # include isolated nodes that match layer filter
    if layers:
        for n, attrs in G.nodes(data=True):
            if attrs.get("layer") in layers and n not in H:
                H.add_node(n, **attrs)

    return H


def generate_pyvis_html(G: nx.DiGraph) -> str:
    net = Network(height="700px", width="100%", directed=True)
    net.toggle_physics(True)

    for nid, attrs in G.nodes(data=True):
        label = attrs.get("label", nid)
        layer = attrs.get("layer", "meta")
        desc = attrs.get("description", "")

        color = {
            "cognition": "#FFB347",
            "symbiosis": "#BEB8EB",
            "meta": "#A3D5FF",
            "meta_process": "#FFD1DC",
            "methodology": "#C3FDB8",
            "theory": "#FFF380",
        }.get(layer, "#DDDDDD")

        tooltip = f"{label} ({layer})<br>{desc}"
        url = None
        if nid in NODE_PATHS:
            url = GITHUB_BASE + NODE_PATHS[nid]

        net.add_node(
            nid,
            label=label,
            color=color,
            title=tooltip,
            url=url,
        )

    for u, v, attrs in G.edges(data=True):
        rel = attrs.get("relation", "")
        net.add_edge(u, v, title=rel, label=rel)

    html_path = ROOT / "meta-graph" / "meta_graph_vis.html"
    net.save_graph(str(html_path))

    with html_path.open("r", encoding="utf-8") as f:
        html = f.read()

    return html


def main():
    st.set_page_config(page_title="EFC Metascope Meta-Graph", layout="wide")

    st.title("EFC Metascope Meta-Knowledge Graph")

    data = load_graph_json()
    G = build_graph(data)

    # ---------- Sidebar filters ----------
    st.sidebar.header("Filters")

    all_layers = sorted({attrs.get("layer", "unknown") for _, attrs in G.nodes(data=True)})
    selected_layers = st.sidebar.multiselect(
        "Layers",
        options=all_layers,
        default=all_layers,
    )

    all_relations = sorted({attrs.get("relation") for _, _, attrs in G.edges(data=True) if attrs.get("relation")})
    selected_relations = st.sidebar.multiselect(
        "Relations",
        options=all_relations,
        default=all_relations,
    )

    Gf = filter_graph(G, selected_layers, selected_relations)

    # ---------- Layout ----------
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Nodes")
        node_rows = []
        for nid, attrs in Gf.nodes(data=True):
            node_rows.append(
                {
                    "id": nid,
                    "label": attrs.get("label"),
                    "layer": attrs.get("layer"),
                    "type": attrs.get("type"),
                }
            )
        st.dataframe(node_rows, use_container_width=True)

    with col2:
        st.subheader("Edges")
        edge_rows = []
        for u, v, attrs in Gf.edges(data=True):
            edge_rows.append(
                {
                    "source": u,
                    "target": v,
                    "relation": attrs.get("relation"),
                }
            )
        st.dataframe(edge_rows, use_container_width=True)

    st.subheader("Graph Visualisation")
    html = generate_pyvis_html(Gf)
    components.html(html, height=720, scrolling=True)

    # ---------- Node inspector ----------
    st.subheader("Node Inspector")

    node_ids = sorted(Gf.nodes())
    if node_ids:
        selected_id = st.selectbox("Select node", node_ids)
        nattrs = Gf.nodes[selected_id]
        st.write("**ID**:", selected_id)
        st.write("**Label**:", nattrs.get("label"))
        st.write("**Layer**:", nattrs.get("layer"))
        st.write("**Type**:", nattrs.get("type"))
        if nattrs.get("description"):
            st.write("**Description**:")
            st.write(nattrs["description"])

        if selected_id in NODE_PATHS:
            rel_path = NODE_PATHS[selected_id]
            url = GITHUB_BASE + rel_path
            st.markdown(f"[Open in GitHub]({url})")


if __name__ == "__main__":
    main()
