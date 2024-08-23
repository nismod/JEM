#!/usr/bin/env python
# coding: utf-8


# home directory on cluster: /soge-home/projects/mistral/jamaica-ccri
# data on cluster is in:
# ./processed_data/boundaries/admin_boundaries.gpkg --> /soge-home/projects/mistral/jamaica-ccri/boundaries/jamaica.gpkg
# ./processed_data/networks/energy/electricity_network_v3.1.gpkg --> /soge-home/projects/mistral/jamaica-ccri/processed_data/networks/energy/electricity_network_v3.2.gpkg


import json
import os
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import shapely
import snail
import snail.intersection
import snail.io

# create an empty 1km grid for Jamaica

# ref: https://github.com/nismod/open-gira/blob/main/workflow/tropical-cyclone/wind_fields/wind_fields.smk#L84
"""
Create an empty TIFF file for a given box specifying the spatial grid to
evaluate network failure
"""

output_path = "/soge-home/projects/mistral/jamaica-ccri/results/grid_failures/jamaica_1km_empty_grid.tiff"


def harmonise_grid(
    minimum: float, maximum: float, cell_length: float
) -> tuple[int, float, float]:
    """
    Grow grid dimensions to encompass whole number of `cell_length`
    Args:
        minimum: Minimum dimension value
        maximum: Maximum dimension value
        cell_length: Length of cell side
    Returns:
        Number of cells
        Adjusted minimum
        Adjusted maximum
    """
    assert maximum > minimum
    span: float = maximum - minimum
    n_cells: int = int(np.ceil(span / cell_length))
    delta: float = n_cells * cell_length - span
    buffer: float = delta / 2
    return n_cells, minimum - buffer, maximum + buffer


filename = "/soge-home/projects/mistral/jamaica-ccri/processed_data/boundaries/jamaica.gpkg"
bounds = gpd.read_file(filename, layer="jamaica")
print(bounds.crs)  # EPSG:3448

# expand grid by buffer
buffer = 100  # in meters (based on crs of bounds)
boundary_box = bounds.bounds
minx, miny, maxx, maxy = boundary_box.values[0]
minx -= buffer
miny -= buffer
maxx += buffer
maxy += buffer
# cell side length in meters (based on crs of bounds)
cell_length = 1000
# determine grid bounding box to fit an integer number of grid cells in each dimension
i, minx, maxx = harmonise_grid(minx, maxx, cell_length)
j, miny, maxy = harmonise_grid(miny, maxy, cell_length)
print(i, j, minx, maxx, miny, maxy)
# create grid as TIFF and save to disk
os.makedirs(os.path.dirname(output_path), exist_ok=True)
command = f"gdal_create -outsize {i} {j} -a_srs EPSG:3448 -a_ullr {minx} {miny} {maxx} {maxy} {output_path}"  # note: projection is hard-coded
os.system(command)

# create grid ids, intersect empty grid with points, get corresponding grid ids for point intersections

# Load the .tiff file
tiff_file_path = "/soge-home/projects/mistral/jamaica-ccri/results/grid_failures/jamaica_1km_empty_grid.tiff"
with rasterio.open(tiff_file_path) as src:
    # Extract grid data
    grid_ids = np.arange(src.width * src.height).reshape((src.height, src.width))
    grid_transform = src.transform
    grid_width = src.width
    grid_height = src.height

# Read the points dataset
points_df = gpd.read_file(
    "/soge-home/projects/mistral/jamaica-ccri/processed_data/networks/energy/electricity_network_v3.2.gpkg",
    layer="nodes",
)
# print(points_df.crs)
points_df["x"] = points_df["geometry"].x
points_df["y"] = points_df["geometry"].y

# Extract coordinates into numpy arrays
x_coords = points_df["x"].to_numpy()
y_coords = points_df["y"].to_numpy()

# Calculate the grid cell indices for each point
cols = ((x_coords - grid_transform.c) / grid_transform.a).astype(int)
rows = ((y_coords - grid_transform.f) / -grid_transform.e).astype(int)

# Add grid cell information to the dataframe
points_df["grid_row"] = rows
points_df["grid_col"] = cols

grid_ids = grid_ids.reshape((grid_height, grid_width))
point_grid_ids = grid_ids[rows, cols]
points_df["grid_ids"] = point_grid_ids
points_df.to_file(
    "/soge-home/projects/mistral/jamaica-ccri/results/grid_failures/jamaica_electricity_nodes_wgrid_ids.gpkg",
    layer="nodes",
    driver="gpkg",
)


# intersect grid with edges using snail library to calculate length of interecting segments
# for the split linestrings get centroids
# get corresponding grid ids for centroids
# merge linestings back, replacing temporary centroids geometry

hazard_paths = [
    "/soge-home/projects/mistral/jamaica-ccri/results/grid_failures/jamaica_1km_empty_grid.tiff"
]
hazard_files = pd.DataFrame({"path": hazard_paths})
hazard_files, grids = snail.io.extend_rasters_metadata(hazard_files)
grid = grids[0]
edges = gpd.read_file(
    "/soge-home/projects/mistral/jamaica-ccri/processed_data/networks/energy/electricity_network_v3.2.gpkg",
    layer="edges",
)
edges = snail.intersection.prepare_linestrings(edges)
grid_intersections = snail.intersection.split_linestrings(edges, grid)
print(edges.crs)  # epsg:3448 is in meters
grid_intersections["length_m"] = grid_intersections["geometry"].length
grid_intersections = snail.intersection.apply_indices(
    grid_intersections, grid, index_i="i_0", index_j="j_0"
)

points_df = gpd.read_file(
    "/soge-home/projects/mistral/jamaica-ccri/results/grid_failures/jamaica_electricity_nodes_wgrid_ids.gpkg",
    layer="nodes",
    # driver="gpkg",
)
lines_df = grid_intersections.copy()
lines_df["geometry"] = lines_df["geometry"].centroid

# Load the .tiff file
tiff_file_path = "/soge-home/projects/mistral/jamaica-ccri/results/grid_failures/jamaica_1km_empty_grid.tiff"
with rasterio.open(tiff_file_path) as src:
    # Extract grid data
    grid_ids = np.arange(src.width * src.height).reshape((src.height, src.width))
    grid_transform = src.transform
    grid_width = src.width
    grid_height = src.height

# print(gdf.crs)
lines_df["x"] = lines_df["geometry"].x
lines_df["y"] = lines_df["geometry"].y

# Extract coordinates into numpy arrays
x_coords = lines_df["x"].to_numpy()
y_coords = lines_df["y"].to_numpy()

# Calculate the grid cell indices for each point
cols = ((x_coords - grid_transform.c) / grid_transform.a).astype(int)
rows = ((y_coords - grid_transform.f) / -grid_transform.e).astype(int)

# Add grid cell information to the dataframe
lines_df["grid_row"] = rows
lines_df["grid_col"] = cols


grid_ids = grid_ids.reshape((grid_height, grid_width))
point_grid_ids = grid_ids[rows, cols]
lines_df["grid_ids"] = point_grid_ids
del lines_df["geometry"]
lines_geo_ = edges[["id", "geometry"]]
lines_df = pd.merge(lines_geo_, lines_df, how="outer", left_on="id", right_on="id")

lines_df.to_file(
    "/soge-home/projects/mistral/jamaica-ccri/results/grid_failures/jamaica_electricity_nodes_wgrid_ids.gpkg",
    layer="edges",
    driver="gpkg",
)


# import matplotlib.pyplot as plt
# fig, ax = plt.subplots()
# points_df[points_df['grid_ids'] == 14969].plot(ax = ax, markersize = 0.3, color = 'red')
# lines_df[lines_df['grid_ids'] == 14969].plot(ax = ax, color = 'blue', alpha = 0.3)
