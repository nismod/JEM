#!/usr/bin/env python
# coding: utf-8
"""Disrupt nodes and edges within a grid

This script uses an arbitrarily defined 1x1km grid, then runs a multi point and
edge failure analysis to evaluate the number of nodes damaged and population
affected. It is a computationally intensive script.

Usage:
    python 002-multi-edge-node-failure.py /soge-home/projects/mistral/jamaica-ccri/ 0 1

    python 002-multi-edge-node-failure.py <base_path> <chunk> <nchunks>

Note: chunk should be an integer in 0..nchunks ; nchunks is the number of chunks so
for example "0 1" will process all grid ids. For more than one, call this script
multiple times: "0 2" and "1 2"
"""
import sys
import functools
import multiprocessing
import os
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.append("../src/")  # required for jem module
from jem.analyse import analyse
from jem.model import jem


def get_empty_results(grid_id):
    return pd.DataFrame(
        {
            "grid_id": grid_id,
            "affected_node_id": [np.nan],
            "affected_node_type": [np.nan],
            "total_nodes_affected": [np.nan],
            "population_affected": [np.nan],
            "demand_affected": [np.nan],
        }
    )


def init_pool(path_to_network, path_to_network_split):
    global nodes
    global edges
    global nodes_split
    global edges_split

    nodes = gpd.read_file(path_to_network, layer="nodes", engine="pyogrio")
    edges = gpd.read_file(path_to_network, layer="edges", engine="pyogrio")

    # use the split network (with linked grid ids) to select failures
    nodes_split = gpd.read_file(path_to_network_split, layer="nodes", engine="pyogrio")
    # note: in the current model nodes of type 'sink' cannot be failed
    nodes_split = nodes_split[nodes_split["asset_type"] != "sink"].copy()
    edges_split = gpd.read_file(path_to_network_split, layer="edges", engine="pyogrio")


def compute_failure(
    grid_id, path_to_network, path_to_flows, output_dir, plot=False, debug=False
):
    nodes_to_attack = nodes_split[nodes_split.grid_ids == grid_id].id.to_list()
    edges_to_attack = edges_split[edges_split.grid_ids == grid_id].id.unique().tolist()

    # run model
    run = jem(
        str(path_to_network),
        str(path_to_network),
        str(path_to_flows),
        print_to_console=False,
        nodes_to_attack=nodes_to_attack,
        edges_to_attack=edges_to_attack,
        super_source=True,
        super_sink=False,
    )
    run.build()
    run.optimise(print_to_console=False)

    # get results
    results = analyse(model_run=run)
    nodes_with_shortfall = results.nodes_with_shortfall().node.to_list()

    if results.nodes_with_shortfall().empty:
        df = get_empty_results(grid_id)
    else:
        population = results.get_population_at_nodes(
            nodes_with_shortfall, col_id="affected_node_id"
        )
        demand = results.get_demand_at_nodes(
            nodes_with_shortfall, col_id="affected_node_id"
        )
        df = population.merge(demand, on="affected_node_id")
        df["grid_id"] = grid_id
        df["population_affected"] = df["population"]
        df["demand_affected"] = df["demand"]
        df = df[
            [
                "grid_id",
                "affected_node_id",
                "population_affected",
                "demand_affected",
            ]
        ]

    if debug:
        results.edge_flows.to_csv(
            output_dir / f"result_arcflows_{grid_id}.csv", index=False
        )

    if plot:
        plot_flows(
            output_dir, results, nodes, edges, nodes_to_attack, edges_to_attack, grid_id
        )

    df.to_csv(output_dir / f"disruption_{grid_id}.csv", index=False)

    print("Done:", grid_id)


def plot_flows(
    output_dir, results, nodes, edges, nodes_to_attack, edges_to_attack, grid_id
):
    edges_idx = edges.set_index(["from_id", "to_id"])
    flows_idx = results.edge_flows.set_index(["from_id", "to_id"])
    edges_with_flows = edges_idx.join(flows_idx)
    edges_with_flows["log_flow"] = log_nonzero(edges_with_flows.flow)

    fig, ax = plt.subplots(figsize=(16, 6))
    ax.set_title(f"Disruption to cell {grid_id}")

    flow_zero = edges_with_flows[(edges_with_flows.flow == 0)]
    if not flow_zero.empty:
        flow_zero.plot(ax=ax, color="#ccc", linewidth=0.1)

    flow_nonzero = edges_with_flows[(edges_with_flows.flow > 0)]
    if not flow_nonzero.empty:
        flow_nonzero.plot(
            ax=ax,
            column="log_flow",
            cmap="viridis_r",
            vmax=10,
            linewidth=0.5,
            legend=True,
        )

    attacked_edges = edges[edges.id.isin(edges_to_attack)]
    if not attacked_edges.empty:
        attacked_edges.plot(ax=ax, color="red", linewidth=0.5)

    attacked_nodes = nodes[nodes.id.isin(nodes_to_attack)]
    if not attacked_nodes.empty:
        attacked_nodes.plot(ax=ax, color="orange")

    plt.savefig(output_dir / f"flows_{grid_id}.png")
    plt.close(fig)


def log_nonzero(x):
    with np.errstate(divide="ignore"):
        return np.log(x, out=np.zeros_like(x), where=0 < x)


if __name__ == "__main__":
    base_path = Path(sys.argv[1])
    chunk = int(sys.argv[2])
    nchunks = int(sys.argv[3])

    if chunk >= nchunks:
        print(f"Skipping {chunk=} >= {nchunks=}")
        sys.exit()

    path_to_flows = (
        base_path / "processed_data/networks/energy/generated_nodal_flows.csv"
    )
    path_to_network = (
        base_path / "processed_data/networks/energy/electricity_network_v3.2.gpkg"
    )
    path_to_network_split = (
        base_path / "results/grid_failures/jamaica_electricity_network_wgrid_ids.gpkg"
    )
    path_to_output = base_path / "results/grid_failures/cell_disruption"
    
    # check if output folder exists, create if not
    if not os.path.exists(path_to_output):
        os.makedirs(path_to_output)

    edges_split = gpd.read_file(path_to_network_split, layer="edges", engine="pyogrio")

    grid_ids = [-1] + sorted(list(edges_split["grid_ids"].unique()))

    n = len(grid_ids)
    n_per_chunk = (n // nchunks) + 1

    from_n = n_per_chunk * chunk
    to_n = n_per_chunk * (chunk + 1)
    if to_n >= n:
        to_n = n

    print(f"Chunks {n=},{chunk=},{nchunks=},{n_per_chunk=}")
    print(f"Processing ids[{from_n}:{to_n}]")

    compute_failure_partial = functools.partial(
        compute_failure,
        path_to_network=path_to_network,
        path_to_flows=path_to_flows,
        output_dir=path_to_output,
        plot=True,
        debug=False,
    )

    with multiprocessing.Pool(
        multiprocessing.cpu_count() // 2,
        initializer=init_pool,
        initargs=(path_to_network, path_to_network_split),
    ) as pool:
        pool.map(compute_failure_partial, grid_ids[from_n:to_n])

    print(f"Done ids[{from_n}:{to_n}]")
