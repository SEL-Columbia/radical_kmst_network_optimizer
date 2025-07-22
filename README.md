# Radical k-MST Network Optimizer

A Mixed Integer Linear Programming (MILP) solver for the k-Minimum Spanning Tree (k-MST) problem using Gurobi optimization.

## Overview

This tool finds the optimal subset of k nodes to connect in a network, minimizing the total connection cost while ensuring all selected nodes form a connected tree rooted at a central node.

## Key Features

- **Efficient k-MST Solution**: Uses directed flow formulation with edge pruning for better performance
- **Scalable**: Supports up to 1,500 nodes
- **Geospatial Output**: Exports results as GeoJSON files for visualization
- **Flexible Input**: Works with any coordinate system (UTM recommended)

## Main Functions

### `milp_kmst(coords, c_coords, k, mip_gap, time_limit)`

Solves the k-MST optimization problem.

**Parameters:**
- `coords`: List/array of candidate node coordinates (excluding root)
- `c_coords`: Root node coordinates  
- `k`: Number of nodes to connect (including root)
- `mip_gap`: MIP gap tolerance for Gurobi solver
- `time_limit`: Maximum solving time in seconds

**Returns:**
- `selected_nodes`: List of selected node labels
- `selected_edges`: List of selected edges with weights

### `save_kmst_results(selected_nodes, selected_edges, coords, c_coords, k, output_folder)`

Exports optimization results to GeoJSON files and summary.

## Requirements

```python
numpy
geopandas
gurobipy
shapely
```

## Quick Start

```python
import numpy as np
from radical_kmst_network_optimizer import milp_kmst, save_kmst_results

# Define coordinates
coords = np.random.rand(50, 2) * 1000  # 50 random points
c_coords = [500, 500]  # Central point
k = 10  # Connect 10 nodes

# Solve
selected_nodes, selected_edges = milp_kmst(coords, c_coords, k, 0.01, 300)

# Save results
save_kmst_results(selected_nodes, selected_edges, coords, c_coords, k)
```

## Output

The solver generates:
- `nodes.geojson`: All nodes with selection status
- `edges.geojson`: Selected network edges
- `summary.txt`: Solution statistics

## License

MIT License 