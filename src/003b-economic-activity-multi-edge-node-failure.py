#!/usr/bin/env python
# coding: utf-8

# ref : https://github.com/nismod/jamaica-infrastructure/blob/7852e914fa6f7c668d5b251677db5ce4d8f6c0df/scripts/analysis/electricity_water_single_point_failure_results_combine.py#L115
# this version is updated for multi-point failure

import pandas as pd

electricity_economic_activity = pd.read_csv(
    "/soge-home/projects/mistral/jamaica-ccri/processed_data/networks_economic_activity/electricity_dependent_economic_activity.csv"
)

gdp_columns = [
    c
    for c in electricity_economic_activity.columns.values.tolist()
    if c not in ("id", "total_GDP", "GDP_unit")
]
electricity_nodes_failure_results = pd.read_csv(
    "/Volumes/T7 Shield/ox_work_current/jamaica/JEM/notebook/ox_jem_test_multi_network_run.csv"
)[["grid_id", "attacked_edge_id", "attacked_node_id", "affected_node_id"]]
electricity_nodes_failures = pd.merge(
    electricity_nodes_failure_results,
    electricity_economic_activity,
    how="left",
    left_on=["affected_node_id"],
    right_on=["id"],
).fillna(0)
electricity_nodes_failures = (
    electricity_nodes_failures.groupby(
        ["grid_id", "attacked_edge_id", "attacked_node_id"]
    )[gdp_columns]
    .sum()
    .reset_index()
)
electricity_nodes_failures["economic_loss"] = electricity_nodes_failures[
    gdp_columns
].sum(axis=1)
electricity_nodes_failures["loss_unit"] = "JD/day"
electricity_nodes_failures.to_csv(
    "/soge-home/projects/mistral/jamaica-ccri/results/grid_failures/multi_point_failure_electricity_nodes_and_edges_economic_losses_no_water.csv",
    index=False,
)
