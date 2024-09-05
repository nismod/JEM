# -*- coding: utf-8 -*-
"""
Created on Mon Oct 18 10:48:38 2021

@author: aqua
"""
from snkit.network import add_topology
from jem.utils import read_data, add_limits_to_edges, add_edge_length, save_data

# define input files
path_to_nodes = "../data/spatial/infrasim-network/version_1.0/nodes.shp"
path_to_edges = "../data/spatial/infrasim-network/version_1.0/edges.shp"


network = read_data(path_to_nodes=path_to_nodes, path_to_edges=path_to_edges)


# network2 = add_component_ids(network)

network2 = network

# drop components
network2.nodes = network2.nodes[network.nodes.component_ == 1].reset_index(drop=True)
network2.edges = network2.edges[network.edges.component_ == 1].reset_index(drop=True)

# adjust voltage column
network2.edges["voltage_kV"] = network2.edges.voltage.str.replace("kV", "").astype(
    "int"
)

# add columns to v1.0

# add columns to v1.0
# ['from_id', 'to_id', 'length', 'min', 'max']
network2 = add_limits_to_edges(network2)
network2 = add_edge_length(network2)
network2 = add_topology(network2, id_col="id")

# define input files
path_to_nodes = "../data/spatial/infrasim-network/version_1.0/nodes_component_1.shp"
path_to_edges = "../data/spatial/infrasim-network/version_1.0/edges_component_1.shp"

save_data(network, path_to_nodes=path_to_nodes, path_to_edges=path_to_edges)
