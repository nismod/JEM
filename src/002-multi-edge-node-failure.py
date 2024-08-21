#!/usr/bin/env python
# coding: utf-8


"""

    This script damages nodes and edges within an arbitrarily defined 1x1km grid (multi point and edge failure analysis) to evaluate
    the number of nodes damaged and population affected. It is a computationally intensive script.

"""

print("-----------------------------------------------------------------")


# --------------
# GLOBAL VARIABLES

restart_mode = False
save_after_iterations = 1
time_script = True

print("Config")
print("------")
print("Restart mode: " + str(restart_mode))
print("Save archive after " + str(save_after_iterations) + " iterations")
print("")

# --------------
# RUN

print("Log")
print("------")

import os
import time
import warnings

import pandas as pd

# from tqdm import tqdm

warnings.simplefilter(action="ignore", category=FutureWarning)

import sys

sys.path.append("../")

from jem.analyse import analyse
from jem.model import jem
from jem.utils import *

# print('imported modules')

results_dataframe = None

path_to_flows = "/soge-home/projects/mistral/jamaica-ccri/processed_data/networks/energy/generated_nodal_flows.csv"
path_to_nodes = "/soge-home/projects/mistral/jamaica-ccri/results/grid_failures/jamaica_electricity_nodes_wgrid_ids.gpkg"
path_to_edges = "/soge-home/projects/mistral/jamaica-ccri/results/grid_failures/jamaica_electricity_nodes_wgrid_ids.gpkg"

nodes = gpd.read_file(path_to_nodes, layer="nodes")
# note: in the current model nodes of type 'sink' cannot be failed
nodes = nodes[nodes["asset_type"] != "sink"]

edges = gpd.read_file(path_to_edges, layer="edges")

# reindex node
try:
    user_input = int(sys.argv[1:][0])
except:
    user_input = 1
if not user_input:
    output_file_path = "/soge-home/projects/mistral/jamaica-ccri/results/grid_failures/node_impact_assessment_"
else:

    def node_indexer(input_arg):
        """return indices to use to sample nodes dataframe for batch run"""
        a = np.linspace(0, 45000, 10)
        return int(a[input_arg - 1]), int(a[input_arg])

    n1, n2 = node_indexer(user_input)
    # nodes = nodes.iloc[n1:n2]#.reset_index(drop=True)
    edges = edges.iloc[n1:n2]
    output_file_path = (
        "/soge-home/projects/mistral/jamaica-ccri/results/grid_failures/node_impact_assessment_batch_"
        + str(user_input)
        + "_iteration_"
    )

grid_ids = list(edges["grid_ids"].unique())[
    0:10
]  # temp sample # TODO: update this after test run on cluster

results_dataframe = pd.DataFrame()

for grid_id in grid_ids:
    nodes_to_attack = nodes[nodes["grid_ids"] == grid_id].id.to_list()
    # print(nodes_to_attack)
    edges_wgrid_ids = list(set(edges[edges["grid_ids"] == grid_id].id.to_list()))
    edges_to_attack = list(set(edges[edges["id"].isin(edges_wgrid_ids)].id.to_list()))
    print(edges_to_attack)

    print("loaded nodes and edges to attack")

    count = 1
    print("beginning loop...")
    if not time_script:
        pass
    else:
        start_time = time.time()

    attacked_edge_types = edges[edges.id.isin(edges_to_attack)]["asset_type"].to_list()
    attacked_node_types = nodes[nodes.id.isin(nodes_to_attack)]["asset_type"].to_list()

    # run model
    run = jem(
        path_to_nodes,
        path_to_edges,
        path_to_flows,
        # timesteps=1,
        print_to_console=False,
        nodes_to_attack=nodes_to_attack,
        edges_to_attack=edges_to_attack,
        super_source=True,
        super_sink=False,
    )
    # build model
    run.build()
    # run model
    run.optimise(print_to_console=False)
    # init results
    results = analyse(model_run=run)
    # get results
    nodes_with_shortfall = results.nodes_with_shortfall().node.to_list()
    # if df is empty, we append blank results
    if results.nodes_with_shortfall().empty == True:
        df = pd.DataFrame(
            {
                "iteration_number": count,
                "grid_id": grid_id,
                "attacked_edge_id": [[edges_to_attack]],
                "attacked_node_id": [[nodes_to_attack]],
                "affected_node_id": [np.nan],
                "attacked_edge_type": [[attacked_edge_types]],
                "attacked_node_type": [[attacked_node_types]],
                "affected_node_type": [np.nan],
                "total_nodes_affected": [np.nan],
                "population_affected": [np.nan],
                "demand_affected": [np.nan],
            }
        )
    else:
        population = results.get_population_at_nodes(
            nodes_with_shortfall, col_id="affected_node_id"
        )
        demand = results.get_demand_at_nodes(
            nodes_with_shortfall, col_id="affected_node_id"
        )
        node_types = results.nodes.loc[
            results.nodes.id.isin(nodes_with_shortfall), "asset_type"
        ].to_list()
        # merge
        df = population.merge(demand, on="affected_node_id")
        print(len(df))
        # add node types
        df["affected_node_type"] = node_types
        # add total number of sinks impacted
        df["total_nodes_affected"] = df.shape[0]
        # add damaged node id
        df["attacked_edge_id"] = [[edges_to_attack]] * df.shape[0]
        df["attacked_node_id"] = [[nodes_to_attack]] * df.shape[0]
        df["attacked_edge_type"] = [[attacked_edge_types]] * df.shape[0]
        df["attacked_node_type"] = [[attacked_node_types]] * df.shape[0]
        df["grid_id"] = grid_id
        # change column naming
        df["iteration_number"] = count
        df["population_affected"] = df[
            "population"
        ]  # TODO: rename instead of reassigning?
        df["demand_affected"] = df["demand"]  # TODO: rename instead of reassigning?
        # reindex
        df = df[
            [
                "iteration_number",
                "grid_id",
                "attacked_edge_id",
                "attacked_node_id",
                "affected_node_id",
                "attacked_edge_type",
                "attacked_node_type",
                "affected_node_type",
                "total_nodes_affected",
                "population_affected",
                "demand_affected",
            ]
        ]
    end_time = time.time()
    time_difference = end_time - start_time
    df["iteration_time_seconds"] = time_difference
    # append
    if results_dataframe.empty:
        results_dataframe = df
    else:
        results_dataframe = pd.concat([results_dataframe, df])
    # append counter
    print("completed iteration " + str(count) + " of " + str(len(edges_to_attack)))
    # save
    # if count % save_after_iterations == 0:
    #     tmp_df = pd.concat([results_dataframe],ignore_index=True)
    # tmp_df.to_csv(output_file_path + str(count) + '.csv',index=False)
    # print('saved archive at iteration number ' + str(count))
    count = count + 1

    print("done")

    print("Saving results...")
    # results_dataframe = pd.concat([results_dataframe],ignore_index=True)

results_dataframe.to_csv(output_file_path + ".csv", index=False)
print("done")

print("-----------------------------------------------------------------")


# TODO: add a section to iterate over all output files and merge them together
results_dataframe.to_csv(
    "/soge-home/projects/mistral/jamaica-ccri/results/grid_failures/ox_jem_multi_network_run.csv"
)
