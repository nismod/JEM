# -*- coding: utf-8 -*-
"""
Created on Mon Oct 18 16:55:18 2021

@author: aqua
"""

import geopandas


# define input files
f1 = "../data/spatial/infrasim-network/version_1.0/nodes.shp"
f2 = "../data/spatial/infrasim-network/nodes.shp"

nodes_1 = geopandas.read_file(f1)
nodes_2 = geopandas.read_file(f2)

cols_original = list(nodes_2.columns)


joined = geopandas.sjoin(nodes_1, nodes_2, how="inner", op="within")

joined["id"] = joined["id_left"]
cols_left = [i for i in joined.columns if "left" in i]
joined = joined.drop(cols_left, axis=1)
joined = joined.drop("id_right", axis=1)
joined.columns = joined.columns.str.replace("_right", "")

joined.to_file("../data/spatial/infrasim-network/nodes_with_id.shp", index=False)


# j = geopandas.overlay(nodes_1, nodes_2, how='union')
# print(j[j.id_1 == j.id_2])
