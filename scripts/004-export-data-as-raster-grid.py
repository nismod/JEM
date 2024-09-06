#!/usr/bin/env python
# coding: utf-8
"""Aggregate and write a directory of grid cell CSV files to raster (GeoTIFFs)

Assumes each CSV file has values to aggregate for a single grid cell, and
that the grid cell ID can be used directly as an integer index into a flattened
ndarray (which is later reshaped back to 2D).

Usage:

    python 004-export-data-as-raster-grid.py /soge-home/projects/mistral/jamaica-ccri/
"""
import sys
from glob import glob
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from tqdm.auto import tqdm


def setup_grid(tiff_file_path):
    with rasterio.open(tiff_file_path) as src:
        grid_ids = src.read(1)
        grid_transform = src.transform
        grid_width = src.width
        grid_height = src.height
        grid_crs = src.crs

    output_kwargs = {
        "driver": "GTiff",
        "count": 1,
        "width": grid_width,
        "height": grid_height,
        "crs": grid_crs,
        "transform": grid_transform,
        "compress": "lzw",
    }

    return grid_ids, output_kwargs


def write_grid(output_path, output_grid, output_kwargs):
    with rasterio.open(output_path, "w", **output_kwargs) as dst:
        dst.write(output_grid, 1)


def read_csvs(csv_dir):
    for csv in tqdm(glob(str(csv_dir / "*.csv"))):
        yield pd.read_csv(csv)


def aggregate_to_grid(dfs, shape, dtype):
    output_grid_flat = np.zeros(
        output_kwargs["height"] * output_kwargs["width"], dtype=dtype
    )

    for df in dfs:
        value = df[varname].sum()
        grid_id = df.loc[0, "grid_id"]
        output_grid_flat[grid_id] = value

    return output_grid_flat.reshape(shape)


if __name__ == "__main__":
    base_path = Path(sys.argv[1])
    ids_tiff = base_path / "results/grid_failures/jamaica_1km_grid_ids.tiff"

    varname = "population_affected"
    dtype = "float32"
    grid_ids, output_kwargs = setup_grid(ids_tiff)
    dfs = read_csvs(base_path / "results/grid_failures/cell_disruption/")
    output_grid = aggregate_to_grid(dfs, grid_ids.shape, dtype)
    output_kwargs["dtype"] = dtype
    out_tiff = base_path / f"results/grid_failures/{varname}.tiff"
    write_grid(out_tiff, output_grid, output_kwargs)

    varname = "demand_affected"
    dtype = "int32"
    grid_ids, output_kwargs = setup_grid(ids_tiff)
    dfs = read_csvs(base_path / "results/grid_failures/cell_disruption/")
    output_grid = aggregate_to_grid(dfs, grid_ids.shape, dtype)
    output_kwargs["dtype"] = dtype
    out_tiff = base_path / f"results/grid_failures/{varname}.tiff"
    write_grid(out_tiff, output_grid, output_kwargs)

    varname = "loss_gdp"
    dtype = "float32"
    grid_ids, output_kwargs = setup_grid(ids_tiff)
    dfs = read_csvs(base_path / "results/grid_failures/cell_disruption_loss/")
    output_grid = aggregate_to_grid(dfs, grid_ids.shape, dtype)
    output_kwargs["dtype"] = dtype
    out_tiff = base_path / f"results/grid_failures/{varname}.tiff"
    write_grid(out_tiff, output_grid, output_kwargs)
