import numpy as np
import os
import geopandas as gpd
import gurobipy as gp
from shapely.geometry import Point, LineString

def _euclid(a, b):
    return float(np.hypot(*(a - b)))

def milp_kmst(coords, c_coords, k, mip_gap, time_limit):
    """
    Solve the k-MST problem with pruned edges and directed flows using Gurobi.

    Args:
        coords (list or np.ndarray): Coordinates of candidate nodes (excluding the root).
        c_coords (tuple or np.ndarray): Coordinates of the root node.
        k (int): Number of nodes to connect (including the root).
        mip_gap (float): MIP gap for Gurobi solver.
        time_limit (float): Time limit for Gurobi solver.

    Returns:
        selected_nodes (list): List of selected node labels (including root).
        selected_edges (list): List of selected edges as (node1, node2, weight).
    """
    num_nodes = len(coords)

    if num_nodes == 0 or num_nodes > 1500:
        if num_nodes == 0:
            print("No candidate nodes provided.")
        else:
            print("Current version of model only supports up to 1500 nodes. Please use smaller node number for this model.")
        return [], []

    # Ensure k is feasible
    if k > num_nodes:
        print(f"This is not feasible, design for total {num_nodes} nodes instead of {k}")
        k = num_nodes

    # Use string for root node for clarity, rest are integers
    root = "C"
    nodes = [root] + list(range(num_nodes))
    node_positions = {root: np.array(c_coords), **{i: np.array(coords[i]) for i in range(num_nodes)}}

    # Precompute distances to root for pruning
    distances_to_root = {node: _euclid(node_positions[node], node_positions[root]) for node in nodes}

    # Build pruned edge list: always keep edges to root, otherwise prune by max distance to root
    edges = []
    for i, node1 in enumerate(nodes):
        for node2 in nodes[i + 1:]:
            edge_weight = _euclid(node_positions[node1], node_positions[node2])
            if node1 == root or node2 == root or edge_weight <= max(distances_to_root[node1], distances_to_root[node2]):
                edges.append((node1, node2, edge_weight))

    # ---------------- Model setup ------------------------------------
    model = gp.Model("kMST_directed")
    model.Params.OutputFlag = 1
    model.Params.MIPGap = mip_gap
    model.Params.TimeLimit = time_limit
    model.Params.VarBranch = 2  # Strong branching (slower but stronger bound tightening)

    # Use gp.GRB for Gurobi constants
    GRB = gp.GRB

    # ---------------- Decision variables -----------------------------
    # Directed arc variables and flows
    arc_variables = {}
    flow_variables = {}
    for (node1, node2, _) in edges:
        arc_variables[(node1, node2)] = model.addVar(vtype=GRB.BINARY, name=f"arc_{node1}_{node2}")
        arc_variables[(node2, node1)] = model.addVar(vtype=GRB.BINARY, name=f"arc_{node2}_{node1}")
        flow_variables[(node1, node2)] = model.addVar(lb=0, ub=k - 1, name=f"flow_{node1}_{node2}")
        flow_variables[(node2, node1)] = model.addVar(lb=0, ub=k - 1, name=f"flow_{node2}_{node1}")
        
        # At most one orientation per edge
        model.addConstr(arc_variables[(node1, node2)] + arc_variables[(node2, node1)] <= 1, name=f"one_dir_{node1}_{node2}")
        # Flow capacity constraints
        model.addConstr(flow_variables[(node1, node2)] <= (k - 1) * arc_variables[(node1, node2)], name=f"flow_cap_{node1}_{node2}")
        model.addConstr(flow_variables[(node2, node1)] <= (k - 1) * arc_variables[(node2, node1)], name=f"flow_cap_{node2}_{node1}")

    node_variables = model.addVars(nodes, vtype=GRB.BINARY, name="node")
    model.addConstr(node_variables["C"] == 1, name="root_selected")

    # ---------------- Objective --------------------------------------
    model.setObjective(gp.quicksum(weight * (arc_variables[(node1, node2)] + arc_variables[(node2, node1)]) 
                                  for (node1, node2, weight) in edges), GRB.MINIMIZE)

    # ---------------- Constraints ------------------------------------
    # Select k-1 nodes (excluding root) and k-1 edges
    model.addConstr(gp.quicksum(node_variables[i] for i in range(num_nodes)) == k - 1, name="k_nodes")
    model.addConstr(gp.quicksum(arc_variables.values()) == k - 1, name="k_edges")

    # Edge can only be selected if both endpoints are selected
    for (node1, node2, _) in edges:
        for arc in [(node1, node2), (node2, node1)]:
            model.addConstr(arc_variables[arc] <= node_variables[node1], name=f"arc_node1_{arc[0]}_{arc[1]}")
            model.addConstr(arc_variables[arc] <= node_variables[node2], name=f"arc_node2_{arc[0]}_{arc[1]}")

    # ---------------- Flow conservation ------------------------------
    # Flow conservation at root: net outflow = k-1
    model.addConstr(
        gp.quicksum(flow_variables[("C", n)] for n in nodes if n != "C" and ("C", n) in flow_variables) -
        gp.quicksum(flow_variables[(n, "C")] for n in nodes if n != "C" and (n, "C") in flow_variables)
        == k - 1, name="root_flow"
    )

    # Flow conservation at other nodes: net flow = node selection
    for node2 in range(num_nodes):
        inflow = gp.quicksum(flow_variables[(node1, node2)] for node1 in nodes
                             if node1 != node2 and (node1, node2) in flow_variables)
        outflow = gp.quicksum(flow_variables[(node2, node1)] for node1 in nodes
                              if node1 != node2 and (node2, node1) in flow_variables)
        model.addConstr(inflow - outflow == node_variables[node2], name=f"flow_cons_{node2}")

    # ---------------- Branch priorities (optional) -------------------
    for arc in arc_variables:
        if "C" in arc:
            arc_variables[arc].BranchPriority = 10  # Higher priority for arcs from/to root
        else:
            arc_variables[arc].BranchPriority = 0   # Default for others

    # ---------------- Solve & extract ------------------------
    model.optimize()

    if model.SolCount == 0:
        return ["C"], []  # No feasible solution

    # Use list comprehension for clarity and efficiency
    selected_nodes = ["C"] + [i for i in range(num_nodes) if node_variables[i].X > 0.5]
    selected_edges = []
    seen_edges = set()
    
    for (node1, node2, weight) in edges:
        if arc_variables[(node1, node2)].X > 0.5 or arc_variables[(node2, node1)].X > 0.5:
            edge_key = tuple(sorted((node1, node2), key=str))
            if edge_key not in seen_edges:
                selected_edges.append((node1, node2, weight))
                seen_edges.add(edge_key)

    return selected_nodes, selected_edges

def save_kmst_results(selected_nodes, selected_edges, coords, c_coords, k, output_folder="output"):
    
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Save all nodes (selected and unselected) as GeoJSON
    nodes_features = []
    selected_set = set(int(n) for n in selected_nodes if n != 'C')
    for i in range(len(coords)):
        geom = Point(coords[i][0], coords[i][1])
        props = {"node_id": i, "selected": i in selected_set}
        nodes_features.append({"geometry": geom, "properties": props})
    # Add node 'C'
    nodes_features.append({
        "geometry": Point(c_coords[0], c_coords[1]),
        "properties": {"node_id": "C", "selected": True}
    })

    # Create GeoDataFrame for nodes and save
    nodes_gdf = gpd.GeoDataFrame(
        [f["properties"] for f in nodes_features],
        geometry=[f["geometry"] for f in nodes_features]
    )
    nodes_gdf.to_file(os.path.join(output_folder, 'nodes.geojson'), driver='GeoJSON')

    # Create edges GeoDataFrame and save
    edges_features = []
    for edge in selected_edges:
        node1, node2, weight = edge
        # Handle if node1 or node2 is 'C'
        if node1 == 'C':
            p1 = c_coords
        else:
            p1 = coords[int(node1)]
        if node2 == 'C':
            p2 = c_coords
        else:
            p2 = coords[int(node2)]
        line_geom = LineString([[p1[0], p1[1]], [p2[0], p2[1]]])
        props = {"node1": node1, "node2": node2, "weight": weight}
        edges_features.append({"geometry": line_geom, "properties": props})

    edges_gdf = gpd.GeoDataFrame(
        [f["properties"] for f in edges_features],
        geometry=[f["geometry"] for f in edges_features]
    )
    edges_gdf.to_file(os.path.join(output_folder, 'edges.geojson'), driver='GeoJSON')

    # Save summary
    summary = f"k: {k}\nnodes_selected: {len(selected_nodes)}\nedges_selected: {len(selected_edges)}\ntotal_weight: {sum(edge[2] for edge in selected_edges)}\nc_coords: {c_coords}"
    with open(os.path.join(output_folder, 'summary.txt'), 'w') as f:
        f.write(summary)

    print(f"Results saved to {output_folder}/: nodes.geojson, edges.geojson, summary.txt")


# test 
if __name__ == "__main__":

    '''
    Example usage: 
    By default, this script generates a random test network around a central point for demonstration.
    To use your own data, replace the sample node generation with your own coordinates (e.g., from a geospatial file).
    Adjust the following as needed:
    - central_x, central_y: coordinates of the central/root node
    - coords: array/list of demand node coordinates (excluding the root)
    - k: number of nodes to connect (including the root)
    - mip_gap: MIP gap for the Gurobi solver
    - time_limit: time limit for the Gurobi solver
    - output_folder: folder to save results

    Note: All coordinates should be in UTM (meters), as the model assumes meter units.
    '''

    # --- Example: Generate random test data (replace with your own data as needed) ---
    central_x, central_y = 0, 0

    # Randomly generate sample nodes around the central point
    np.random.seed(42)
    num_sample_nodes = 100
    radius = 1000

    angles = np.random.uniform(0, 2 * np.pi, num_sample_nodes)
    radii = np.random.uniform(0, radius, num_sample_nodes)
    sample_x = central_x + radii * np.cos(angles)
    sample_y = central_y + radii * np.sin(angles)
    coords = np.column_stack([sample_x, sample_y])
    c_coords = [central_x, central_y]
    # --------------------------------------------------------------------------------

    # Parameters (edit as needed)
    k = 20             # number of nodes to connect (including the root)
    mip_gap = 0.01      # MIP gap for the Gurobi solver
    time_limit = 300    # time limit for the Gurobi solver (seconds)

    # Run the model
    nodes, edges = milp_kmst(coords, c_coords, k, mip_gap, time_limit)

    print(nodes, edges)
    
    if len(edges) > 0:
        save_kmst_results(nodes, edges, coords, c_coords, k, output_folder="output")
    else:
        print("No solution found or problem infeasible.")