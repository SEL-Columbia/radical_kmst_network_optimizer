# Radical k-MST Network Optimizer

## Background & Motivation

This code was developed during research on community network design in Sub-Saharan Africa. We assumed **average per-node connection costs vary with the number of nodes connected** in a community network. For example, a community with clustered households and small businesses may require only **15m of low-voltage (LV) wire per node** to connect the concentrated area. When expanding to connect more dispersed households throughout the community, the LV wire requirement can increase to **30m per node or more**. This represents the simplest case. More complex and interesting scenarios should exist in real communities.

### The Problem

Given a community with scattered demand node locations (households, businesses, etc.), we decide:

1. **A strategic center** as the network root - this could be: trading center, generation set location, main productive load facility, health facilities, other community anchor points ... 

2. **The number k of demand nodes to connect** by adjusting the k parameter to analyze different community coverage scenarios and their associated electric wire requirements

And, the model designs the network connecting k nodes with the least length of electric wire requirement. 

### Applications & Insights

The optimization results provide valuable proxies and estimations for electrification planning, such as:

- **Phased rollout strategies** - Determine optimal sequencing for connecting households as budgets become available
- **Infrastructure investment planning** - Estimate total wire requirements for different coverage scenarios
- **Per-household connection costs** at various scales (e.g., cost curves showing how unit costs change from 20 to 50 to 100 connected homes). This would be an important metric to consider when doing electrification planning. Also, the marginal cost insights of the network at different scales.

This makes the tool valuable for strategic planning around rural electrification and energy access policy. However, this model is purely mathematical, calculating proxies without incorporating physical infrastructure constraints or local demand variations. It treats every demand node with equal weight and does not consider line capacity limitations. For more detailed network planning, additional physical constraints and localized demand data should be integrated into the model.

---

## Technical Overview (Gurobi License Required)

A Mixed Integer Linear Programming (MILP) solver for the k-Minimum Spanning Tree (k-MST) problem using Gurobi optimization. This tool finds the optimal subset of k nodes to connect in a network, minimizing the total connection cost while ensuring all selected nodes form a connected tree rooted at a central node.

### Key Features

- **Efficient k-MST Solution**: Uses directed flow formulation with edge pruning for better performance
- **Scalable**: Supports up to 1,500 nodes
- **Geospatial Output**: Exports results as GeoJSON files

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

## Requirements

```python
numpy
geopandas
gurobipy
shapely
```

## Quick Start

```python
python radical_kmst_network_optimizer.py
```
The code includes randomly generated sample demand nodes for illustration purposes. Always replace this section with your own data when adapting the tool for your specific use case.

## Output

The solver generates:
- `nodes.geojson`: All nodes with selection status
- `edges.geojson`: Selected network edges
- `summary.txt`: Solution statistics
