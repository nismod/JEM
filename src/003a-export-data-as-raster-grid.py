#!/usr/bin/env python
# coding: utf-8

import os

import numpy as np
import pandas as pd
import rasterio

# tiff_file_path = "/soge-home/projects/mistral/jamaica-ccri/results/grid_failures/jamaica_1km_empty_grid.tiff"
# with rasterio.open(tiff_file_path) as src:
#     # Extract grid data
#     grid_ids = np.arange(src.width * src.height).reshape((src.height, src.width))
#     grid_transform = src.transform
#     grid_width = src.width
#     grid_height = src.height
#     # grid_ids = grid_ids.reshape((grid_height, grid_width))

tiff_file_path = "/soge-home/projects/mistral/jamaica-ccri/results/grid_failures/jamaica_1km_grid_ids.tiff"
with rasterio.open(tiff_file_path) as src:
    grid_ids = src.read(1)
    grid_transform = src.transform
    grid_width = src.width
    grid_height = src.height

# read in results
results_dataframe = pd.read_csv(
    "/soge-home/projects/mistral/jamaica-ccri/results/grid_failures/ox_jem_multi_network_impact_assessment.csv"
)

results_dataframe["grid_id"] = results_dataframe["grid_id"].astype(int)
group = results_dataframe.groupby(["grid_id"]).agg({"population_affected": "sum"})
group["population_affected"] = group["population_affected"].fillna(0)
group.reset_index(inplace=True)
# create lookup dictionary
value_dict = pd.Series(
    results_dataframe["population_affected"].values, index=results_dataframe["grid_id"]
).to_dict()

# prepare output array
output_grid = np.zeros((grid_height, grid_width), dtype=np.float32)

# update values in output_grid based on grid_ids and value_dict
for grid_id, population in value_dict.items():
    mask = grid_ids == grid_id
    output_grid[mask] = population

# for index, row in group.iterrows():
#     grid_ids[grid_ids == row["grid_id"]] = row["population_affected"]

# filepath for original empty grid
dataset = r"/soge-home/projects/mistral/jamaica-ccri/results/grid_failures/jamaica_1km_empty_grid.tiff"

# Outfile path
outpath = r"/soge-home/projects/mistral/jamaica-ccri/results/grid_failures/"

# # Open raster
# raster = rasterio.open(dataset)

# band = raster.read(1)

# # Write to TIFF
# kwargs = raster.meta
# kwargs.update(dtype=rasterio.float32, count=1, compress="lzw")

# with rasterio.open(
#     os.path.join(outpath, "jamaica_1km_affected_population_grid.tiff"), "w", **kwargs
# ) as dst:  # TODO: hard-coded atm
#     # TODO: test to write multiple bands at the same time / add bands to the same raster file
#     dst.write_band(1, grid_ids.astype(rasterio.float32))

kwargs = {
    "driver": "GTiff",
    "count": 1,
    "dtype": "float32",
    "width": grid_width,
    "height": grid_height,
    "crs": src.crs,  # use CRS from the original TIFF
    "transform": grid_transform,
    "compress": "lzw",
}

with rasterio.open(
    os.path.join(outpath, "jamaica_1km_affected_population_grid.tiff"), "w", **kwargs
) as dst:
    dst.write(output_grid, 1)
