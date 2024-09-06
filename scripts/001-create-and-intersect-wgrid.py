#!/usr/bin/env python
# coding: utf-8
"""Set up hotspots grid, then split power network lines and nodes

1. create an empty 1km grid for Jamaica. Create an empty TIFF file for a given
   box specifying the spatial grid to evaluate network failure, create integer
   grid IDs for each cell.
2. assign grid IDs to power network nodes and (split) edges


See also, for grid creation:
https://github.com/nismod/open-gira/blob/main/workflow/tropical-cyclone/wind_fields/wind_fields.smk#L84

Data
----

Inputs:

- ./processed_data/boundaries/jamaica.gpkg
- ./processed_data/networks/energy/electricity_network_v3.2.gpkg

Outputs:

- ./results/grid_failures/jamaica_1km_empty_grid.tiff
- ./results/grid_failures/jamaica_1km_grid_ids.tiff
- ./results/grid_failures/jamaica_electricity_network_wgrid_ids.gpkg

Usage
-----

To run on SoGE cluster:

    python 001-create-and-intersect-wgrid.py /soge-home/projects/mistral/jamaica-ccri

To run locally with a relative path, ensure all inputs are available, then:

    python 001-create-and-intersect-wgrid.py ./data/dir

"""
import os
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import snail
import snail.io


def main(base_path):
    # base_path = Path("/soge-home/projects/mistral/jamaica-ccri/")
    base_path = Path(base_path)

    # input paths
    boundary_file_path = base_path / "processed_data/boundaries/jamaica.gpkg"

    # output paths
    empty_grid_path = base_path / "results/grid_failures/jamaica_1km_empty_grid.tiff"
    grid_id_tiff_path = base_path / "results/grid_failures/jamaica_1km_grid_ids.tiff"

    create_grid(grid_id_tiff_path, boundary_file_path, empty_grid_path)
    grid, hazard_files = read_grid(grid_id_tiff_path)
    intersect_grid_with_nodes(base_path, grid, hazard_files)
    intersect_grid_with_edges(base_path, grid, hazard_files)


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


def create_grid(grid_id_tiff_path, boundary_file_path, empty_grid_path):
    bounds = gpd.read_file(boundary_file_path, layer="jamaica")

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

    # create grid as TIFF and save to disk
    os.makedirs(os.path.dirname(empty_grid_path), exist_ok=True)
    command = f"gdal_create -outsize {i} {j} -a_srs EPSG:3448 -a_ullr {minx} {miny} {maxx} {maxy} {empty_grid_path}"  # note: projection is hard-coded
    os.system(command)

    # Load the .tiff file
    with rasterio.open(empty_grid_path) as src:
        # Extract grid data
        grid_ids = np.arange(src.width * src.height).reshape((src.height, src.width))
        grid_transform = src.transform
        grid_width = src.width
        grid_height = src.height

    # Export grid_ids as .tiff file
    with rasterio.open(
        grid_id_tiff_path,
        "w",
        driver="GTiff",
        height=grid_height,
        width=grid_width,
        count=1,
        dtype=rasterio.uint32,
        crs=src.crs,
        transform=grid_transform,
    ) as dst:
        dst.write(grid_ids.astype(rasterio.uint32), 1)


def read_grid(grid_id_tiff_path):
    hazard_paths = [grid_id_tiff_path]
    hazard_files = pd.DataFrame({"path": hazard_paths})
    hazard_files["key"] = [Path(path).stem for path in hazard_paths]
    hazard_files, grids = snail.io.extend_rasters_metadata(hazard_files)
    grid = grids[0]
    return grid, hazard_files


def intersect_grid_with_nodes(base_path, grid, hazard_files):
    points_df = gpd.read_file(
        base_path / "processed_data/networks/energy/electricity_network_v3.2.gpkg",
        layer="nodes",
    )
    grid_intersections_p = snail.intersection.apply_indices(
        points_df, grid, index_i="i_0", index_j="j_0"
    )
    grid_intersections_p = snail.io.associate_raster_files(
        grid_intersections_p, hazard_files
    )
    grid_intersections_p.rename(
        columns={"jamaica_1km_grid_ids": "grid_ids"}, inplace=True
    )
    grid_intersections_p.to_file(
        base_path / "results/grid_failures/jamaica_electricity_network_wgrid_ids.gpkg",
        layer="nodes",
        driver="gpkg",
    )


def intersect_grid_with_edges(base_path, grid, hazard_files):
    edges = gpd.read_file(
        base_path / "processed_data/networks/energy/electricity_network_v3.2.gpkg",
        layer="edges",
    )
    edges = snail.intersection.prepare_linestrings(edges)
    grid_intersections_l = snail.intersection.split_linestrings(edges, grid)
    grid_intersections_l["length_m"] = grid_intersections_l["geometry"].length
    grid_intersections_l = snail.intersection.apply_indices(
        grid_intersections_l, grid, index_i="i_0", index_j="j_0"
    )
    grid_intersections_l = snail.io.associate_raster_files(
        grid_intersections_l, hazard_files
    )
    grid_intersections_l.rename(
        columns={"jamaica_1km_grid_ids": "grid_ids"}, inplace=True
    )
    grid_intersections_l.to_file(
        base_path / "results/grid_failures/jamaica_electricity_network_wgrid_ids.gpkg",
        layer="edges",
        driver="gpkg",
    )


if __name__ == "__main__":
    try:
        base_path = sys.argv[1]
    except IndexError:
        print(f"Usage: python {__file__} ./path/to/data/directory")
    main(base_path)
