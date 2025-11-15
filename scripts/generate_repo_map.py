import os
from pyvis.network import Network
import networkx as nx

def build_tree_graph(root="."):
    G = nx.DiGraph()

    for dirpath, dirnames, filenames in os.walk(root):
        # Skip system dirs
        if any(skip in dirpath for skip in [
            "/.git", "/.github", "__pycache__", "/lib", "/.vscode"
        ]):
            continue

        rel = os.path.relpath(dirpath, root)
        G.add_node(rel, title=rel, level=rel.count("/"))

        parent = os.path.dirname(rel)
        if parent and parent != ".":
            G.add_edge(parent, rel)

        for f in filenames:
            fpath = os.path.join(rel, f)
            if f.endswith((".png", ".jpg", ".pdf")):
                continue
            G.add_node(fpath, title=fpath, level=rel.count("/") + 1)
            G.add_edge(rel, fpath)

    return G

def generate_visualization(G, output_html="output/repo_map.html"):
    net = Network(height="900px", width="100%", directed=True)
    net.repulsion(node_distance=180, central_gravity=0.3, spring_length=140)

    for node, data in G.nodes(data=True):
        level = data.get("level", 0)
        size = 15 + level * 2
        net.add_node(node, label=node, title=node, size=size)

    for src, dst in G.edges():
        net.add_edge(src, dst)

    # Use write_html() explicitly for Codespaces compatibility
    net.write_html(output_html)
    print(f"✓ Created interactive HTML map: {output_html}")

def main():
    print("Generating repository map...")
    G = build_tree_graph(".")
    generate_visualization(G)

if __name__ == "__main__":
    main()
