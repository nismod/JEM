#!/usr/bin/env python
# coding: utf-8
"""Disrupt nodes and edges within a grid

This script uses an arbitrarily defined 1x1km grid, then runs a multi point and
edge failure analysis to evaluate the number of nodes damaged and population
affected. It is a computationally intensive script.
"""
import functools
import multiprocessing
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
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


def init_pool(path_to_network):
    global nodes
    global edges
    global flows

    # note: in the current model nodes of type 'sink' cannot be failed
    nodes = gpd.read_file(path_to_network, layer="nodes", engine="pyogrio")
    nodes = nodes[nodes["asset_type"] != "sink"].copy()
    edges = gpd.read_file(path_to_network, layer="edges", engine="pyogrio")
    flows = pd.read_csv(flows)


def compute_failure(grid_id, path_to_network, path_to_flows, output_file_path):

    nodes_to_attack = nodes[nodes.grid_ids == grid_id].id.to_list()
    edges_to_attack = edges[edges.grid_ids == grid_id].id.unique().tolist()

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

    df.to_csv(f"{output_file_path}_{grid_id}.csv", index=False)
    print("Done:", grid_id)


if __name__ == "__main__":
    # base_path = Path("/soge-home/projects/mistral/jamaica-ccri/")
    base_path = Path("./data/ccri")
    path_to_flows = (
        base_path / "processed_data/networks/energy/generated_nodal_flows.csv"
    )
    path_to_network = (
        base_path / "results/grid_failures/jamaica_electricity_network_wgrid_ids.gpkg"
    )
    path_to_output = base_path / "results/grid_failures/disruption"

    edges = gpd.read_file(path_to_network, layer="edges")

    grid_ids = list(edges["grid_ids"].unique())

    compute_failure_partial = functools.partial(
        compute_failure,
        path_to_network=path_to_network,
        path_to_flows=path_to_flows,
        output_file_path=path_to_output,
    )

    with multiprocessing.Pool(
        initializer=init_pool, initargs=(path_to_network,)
    ) as pool:
        pool.map(compute_failure_partial, grid_ids, chunksize=1024)
