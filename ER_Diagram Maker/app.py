import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.patches import Rectangle, Ellipse, Polygon

# Initialize Graph
G = nx.Graph()

# Define Entities, Attributes, and Relationships
entities = ["Customer", "Order", "Supplier", "Product", "payment", "manager"]
attributes = {
    "Customer": ["Cust_ID", "Name", "Phone"],
    "Order": ["Order_ID", "Date"],
    "Supplier": ["Supp_ID", "Company"],
    "Product": ["Prod_ID", "Price"],
    "payment": ["online", "cash"],
    "manager": ["manager_ID", "Name"]
}
relationships = ["Places", "Supplies", "Contains", "way","check"]

# Add nodes to Graph
for entity in entities:
    G.add_node(entity)

for attr_list in attributes.values():
    for attr in attr_list:
        G.add_node(attr)

for rel in relationships:
    G.add_node(rel)

# Define edges (connect entities to relationships & attributes to entities)
edges = [
    ("Customer", "Places"), ("Order", "Places"),
    ("Supplier", "Supplies"), ("Product", "Supplies"),
    ("Order", "Contains"), ("Product", "Contains"),
    ("payment", "way"), ("Customer", "way"),
    ("manager", "check"), ("Oder", "check") # Fixed typo here (case-sensitive issue)
]
for entity, attrs in attributes.items():
    for attr in attrs:
        edges.append((entity, attr))

G.add_edges_from(edges)

# Define layout
pos = nx.spring_layout(G, seed=50)

# Draw edges
plt.figure(figsize=(12, 8))  # Increase figure size for better readability
nx.draw_networkx_edges(G, pos, edge_color="black", width=1.5, alpha=0.7)

# Draw nodes with larger shapes manually
ax = plt.gca()

for node, (x, y) in pos.items():
    if node in entities:
        ax.add_patch(Rectangle((x - 0.08, y - 0.06), 0.19, 0.12, color="lightgreen", ec="black", lw=1.8))  # Larger rectangle
    elif node in relationships:
        ax.add_patch(Polygon([(x, y + 0.08), (x + 0.08, y), (x, y - 0.08), (x - 0.08, y)], 
                             color="green", ec="black", lw=1.8))  # Larger diamond
    else:
        ax.add_patch(Ellipse((x, y), 0.15, 0.08, color="seagreen", ec="black", lw=1.8))  # Larger ellipse

# Draw labels with adjusted font size
for node, (x, y) in pos.items():
    plt.text(x, y, node, fontsize=10, ha='center', va='center', fontweight="bold")

# Final settings
plt.title("ER Diagram with Larger Shapes", fontsize=14, fontweight="bold")
plt.axis("off")
plt.show()
