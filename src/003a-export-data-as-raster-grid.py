#!/usr/bin/env python
# coding: utf-8

import os

import numpy as np
import pandas as pd
import rasterio

tiff_file_path = "/soge-home/projects/mistral/jamaica-ccri/results/grid_failures/jamaica_1km_empty_grid.tiff"
with rasterio.open(tiff_file_path) as src:
    # Extract grid data
    grid_ids = np.arange(src.width * src.height).reshape((src.height, src.width))
    grid_transform = src.transform
    grid_width = src.width
    grid_height = src.height
    grid_ids = grid_ids.reshape((grid_height, grid_width))
grid_id_df = pd.DataFrame(grid_ids.flatten())
grid_id_df.rename(columns={0: "grid_id"}, inplace=True)
# read in results
results_dataframe = pd.read_csv(
    "/soge-home/projects/mistral/jamaica-ccri/results/grid_failures/ox_jem_multi_network_run.csv"
)
merge = pd.merge(
    grid_id_df, results_dataframe, how="left", right_on="grid_id", left_on="grid_id"
)
merge = merge.groupby(["grid_id"]).agg({"population_affected": "sum"})
merge["population_affected"] = merge["population_affected"].fillna(0)
merge.reset_index(inplace=True)
for index, row in merge.iterrows():
    grid_ids[grid_ids == row["grid_id"]] = row["population_affected"]

# filepath for original empty grid
dataset = r"/soge-home/projects/mistral/jamaica-ccri/results/grid_failures/jamaica_1km_empty_grid.tiff"

# Outfile path
outpath = r"/soge-home/projects/mistral/jamaica-ccri/results/"

# Open raster
raster = rasterio.open(dataset)

band = raster.read(1)

# Write to TIFF
kwargs = raster.meta
kwargs.update(dtype=rasterio.float32, count=1, compress="lzw")

with rasterio.open(
    os.path.join(outpath, "jamaica_1km_affected_population_grid.tiff"), "w", **kwargs
) as dst:  # TODO: hard-coded atm
    # TODO: test to write multiple bands at the same time / add bands to the same raster file
    dst.write_band(1, grid_ids.astype(rasterio.float32))
