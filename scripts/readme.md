# Grid Processing Scripts for Jamaica

This repository contains a series of Python scripts designed to perform various operations on an arbitrary grid covering Jamaica. Each script is focused on a specific task related to grid manipulation, node and edge failures, economic activity analysis, and the creation of hotspots maps to identify critical areas. Below is a brief overview of each script and its functionality.

## Table of Contents
- [001-create-and-intersect-wgrid.py](#001-create-and-intersect-wgridpy)
- [002-multi-edge-node-failure.py](#002-multi-edge-node-failurepy)
- [003-economic-activity-multi-edge-node-failure.py](#003-economic-activity-multi-edge-node-failurepy)
- [004-export-data-as-raster-grid.py](#004-export-data-as-raster-gridpy)

## 001-create-and-intersect-wgrid.py

This script creates an arbitrary grid that covers the entire country of Jamaica. It generates unique identifiers for each grid cell and intersects these grid cells with existing points and lines to populate a new column named `grid_id`.

### Overview
- Generates a grid for Jamaica.
- Assigns unique IDs to each grid cell.
- Intersects grid cells with points and lines to determine the corresponding `grid_id`.

---

## 002-multi-edge-node-failure.py

This script simulates the simultaneous failure of nodes and edges within a grid cell. It uses parallel processing for efficiency. 

### Running on Cluster
To run this script on a cluster using the SLURM job scheduler, refer to `run_002_chunks.sh`.

### Overview
- Simulates failures of multiple nodes and edges.
- Utilises parallel processing for enhanced performance.
- Provides instructions for running on a cluster.

---

## 003-economic-activity-multi-edge-node-failure.py

This script computes economic activity at the grid cell level. It analyses the impact of multi-edge and node failures on economic metrics within each grid cell.

### Overview
- Calculates economic activity metrics for each grid cell.
- Analyses the effects of grid cell (node and edge) failures on economic values.

---

## 004-export-data-as-raster-grid.py

This script exports computed values from the analysis as individual raster files in `.tiff` format. This is useful for visualising and further analysing the data e.g. hotspot maps.

### Overview
- Exports data as raster files.
- Supports the `.tiff` file format for compatibility with GIS applications.

---

## Usage

To run any of these scripts, ensure you have the necessary dependencies installed. Instructions for setting up the environment can be found in the `environment.yml` file.

