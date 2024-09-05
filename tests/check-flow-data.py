# -*- coding: utf-8 -*-
"""
Created on Tue Oct 19 14:49:22 2021

@author: aqua
"""
from jem.model import jem
from jem.utils import get_flow_nodes

path_to_flows = "../data/csv/generated_nodal_flows.csv"
path_to_nodes = "../data/spatial/infrasim-network/version_1.0/nodes_component_1.shp"
path_to_edges = "../data/spatial/infrasim-network/version_1.0/edges_component_1.shp"

# check flow data
network = jem(path_to_nodes, path_to_edges, path_to_flows)
nodes = get_flow_nodes(network.nodes)
