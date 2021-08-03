'''

    sample.py
    
        A script to sample a small subset of the Jamaican power grid data
            for testing. The sample is taken for a given parish.

'''


import geopandas as gpd

# File paths
path_to_edges = '../data/spatial/edges.shp'
path_to_nodes = '../data/spatial/nodes.shp'

# Read edges and nodes
edges = gpd.read_file(path_to_edges)
nodes = gpd.read_file(path_to_nodes)

sample = ['St. James']

# sample
nodes = nodes.loc[nodes.parish.isin(sample)].reset_index(drop=True)
edges = edges.loc[edges.parish.isin(sample)].reset_index(drop=True)

nodes.to_file(driver='ESRI Shapefile', filename='../data/demo/nodes_demo.shp')
edges.to_file(driver='ESRI Shapefile', filename='../data/demo/edges_demo.shp')