# Radical k-MST Network Optimizer

## Background & Motivation

This code was developed during research on community network design in Sub-Saharan Africa. The core insight driving this work is that **average per-node connection costs vary significantly with the number of nodes connected** in a community network.

For example:
- A community with clustered households and small businesses may require only **15m of low-voltage (LV) wire per node** to connect the concentrated area
- When expanding to connect more dispersed households throughout the community, the LV wire requirement can increase to **30m per node or more**

### The Problem

Given a community with scattered demand nodes (households, businesses, etc.), we decide:

1. **a strategic center** as the network root - this could be:
   - Trading center
   - Generation set location  
   - Main productive load facility
   - Health facilities
   - Other community anchor points

2. **number of the demand nodes to connect (k)** by easily changing k to analyze different community coverage scenarios and their associated per-node costs

This tool enables community energy planners to optimize network topology and understand the cost implications of connecting different numbers of households.


### Applications & Insights

The optimization results provide valuable proxies and estimations for:

**Electrification Planning:**
- **Phased rollout strategies** - Determine optimal sequencing for connecting households as budgets become available
- **Grid extension feasibility** - Compare connection costs against standalone solar/battery alternatives
- **Infrastructure investment planning** - Estimate total wire/cable requirements for different coverage scenarios
- **Per-household connection costs** at various scales (e.g., cost curves showing how unit costs change from 10 to 50 to 100 connected homes)
- **Marginal cost insights** - Understand the cost of connecting each additional household

This makes the tool valuable for strategic planning around rural electrification and energy access policy. However, this model is purely mathematical, calculating proxies without incorporating physical infrastructure constraints or local demand variations. It treats every demand node with equal weight and does not consider line capacity limitations. For more detailed network planning, additional physical constraints and localized demand data should be integrated into the model.

---

## Technical Overview

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
