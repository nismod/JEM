'''

map_demand_with_voronoi.py

    This script takes the output from create_topology.py and appends population and
     electricity intensity data to the nodal file. It appends population data based on the 
     voronoi projection of sink nodes within each Parish. The voronoi is also saved as an output.

'''

import pandas as pd
import geopandas as gpd
import numpy as np
from scipy.spatial import Voronoi
from shapely.geometry import Polygon

from utils import *

import sys
sys.path.append('../jamaica-infrastructure')

from scripts.preprocess.preprocess_utils import \
assign_node_weights_by_population_proximity,\
voronoi_finite_polygons_2d,extract_nodes_within_gdf,assign_value_in_area_proportions


# setup params
epsg=3448
node_id_column='id'
population_id_column='population'

# read data
master_nodes = gpd.read_file('../data/spatial/infrasim-network/nodes.shp')
parish_boundaries = gpd.read_file('../data/spatial/else/admin-boundaries.shp')
population_dataframe = gpd.read_file('../data/population-russell/population.gpkg')

# rename
master_nodes.parish = master_nodes.parish.str.replace('St. Andrew','KSA')
parish_boundaries.Parish = parish_boundaries.Parish.str.replace('St','St')

# get sinks
sinks = master_nodes[master_nodes['asset_type'] == 'sink'].reset_index(drop=True).copy()

# change crs
master_nodes = master_nodes.to_crs(epsg=epsg)
sinks = sinks.to_crs(epsg=epsg)
parish_boundaries = parish_boundaries.to_crs(epsg=epsg)
population_dataframe = population_dataframe.to_crs(epsg=epsg)

# begin loop
combined_voronoi = []
combined_nodes = []

for unique_parish in sinks.parish.unique():
    nodes_dataframe = sinks.loc[sinks.parish.isin([unique_parish])].reset_index(drop=True).copy()
    #population_dataframe = pop_bound.loc[pop_bound.PARISH.isin([unique_parish])].reset_index(drop=True).copy()
    parish_dataframe = parish_boundaries.loc[parish_boundaries.Parish.isin([unique_parish])].reset_index(drop=True).copy()

    # create Voronoi polygons for the nodes
    xy_list = []
    for iter_, values in nodes_dataframe.iterrows():
        xy = list(values.geometry.coords)
        xy_list += [list(xy[0])]

    vor = Voronoi(np.array(xy_list))
    regions, vertices = voronoi_finite_polygons_2d(vor)
    min_x = vor.min_bound[0] - 0.1
    max_x = vor.max_bound[0] + 0.1
    min_y = vor.min_bound[1] - 0.1
    max_y = vor.max_bound[1] + 0.1

    mins = np.tile((min_x, min_y), (vertices.shape[0], 1))
    bounded_vertices = np.max((vertices, mins), axis=0)
    maxs = np.tile((max_x, max_y), (vertices.shape[0], 1))
    bounded_vertices = np.min((bounded_vertices, maxs), axis=0)

    box = Polygon([[min_x, min_y], [min_x, max_y], [max_x, max_y], [max_x, min_y]])

    poly_list = []
    for region in regions:
        polygon = vertices[region]
        # Clipping polygon
        poly = Polygon(polygon)
        poly = poly.intersection(box)
        poly_list.append(poly)

    poly_index = list(np.arange(0, len(poly_list), 1))

    poly_df = pd.DataFrame(list(zip(poly_index, poly_list)),
                                   columns=['gid', 'geometry'])

    gdf_voronoi = gpd.GeoDataFrame(poly_df, geometry = 'geometry') #,crs=f'epsg:{epsg}'
    # add area
    gdf_voronoi['area'] = gdf_voronoi.apply(lambda x:x.geometry.area,axis=1)
    # add nodes
    gdf_voronoi[node_id_column] = gdf_voronoi.progress_apply(    
            lambda row: extract_nodes_within_gdf(row['geometry'],nodes_dataframe,node_id_column),axis=1)
    
    # add parish
    gdf_voronoi['Parish'] = gdf_voronoi[node_id_column].map(nodes_dataframe.set_index('id')['parish'].to_dict())
    
    # rename geom cols
    gdf_voronoi['voronoi_geom'] = gdf_voronoi['geometry']
    parish_dataframe['parish_geom'] = parish_dataframe['geometry']
    
    # dissolve
    gdf_voronoi = pd.merge(gdf_voronoi,parish_dataframe[['Parish','parish_geom']],
                           how='left',on='Parish')
    
    # dropna/empty
    gdf_voronoi = gdf_voronoi[~gdf_voronoi.parish_geom.isna()].reset_index(drop=True)
    
    try:
        gdf_voronoi['geometry'] = gdf_voronoi.progress_apply(lambda row: \
                    (row.voronoi_geom.buffer(0)).intersection(row.parish_geom.buffer(0)),axis=1)
    except:
       print('FAILED: ' + unique_parish)
    
    combined_voronoi.append(gdf_voronoi)
    combined_nodes.append(nodes_dataframe)
    
# concat
voronois = gpd.GeoDataFrame( pd.concat( combined_voronoi, ignore_index=True) )
nodes = gpd.GeoDataFrame( pd.concat( combined_nodes, ignore_index=True) ) 
# reindex
voronois = voronois[['id','area','Parish','geometry']]
voronois = voronois[~voronois.geometry.is_empty].reset_index(drop=True)
# add population metrics
voronois[population_id_column] = 0
voronois = assign_value_in_area_proportions(population_dataframe, voronois, population_id_column)
voronois = voronois[~(voronois[node_id_column] == '')]

# append
gdf_pops = voronois.copy()
new_nodes = pd.merge(nodes, gdf_pops, how='left', on=[node_id_column])
#remap
pop_mapped = new_nodes.set_index('id')['population'].to_dict()
# reassign
master_nodes['population'] = master_nodes['id'].map(pop_mapped).fillna(0)
# rename parish
voronois['parish'] = voronois['Parish']

# save
voronois = voronois[['id','parish','area','population','geometry']]
voronois = voronois[~voronois.geometry.is_empty].reset_index(drop=True)
voronois.to_file(driver='ESRI Shapefile',filename='../data/spatial/infrasim-network/voronoi.shp')
nodes.to_file(driver='ESRI Shapefile',filename='../data/spatial/infrasim-network/voronoi_nodes.shp')

# append energy intensity data
boundaries = get_ei_by_parish()
# create dict
ei_dict = boundaries.set_index('PARISH')['ei'].to_dict()

# rename parishes
boundaries.PARISH = boundaries.PARISH.str.replace('Kingston','KSA')
boundaries.PARISH = boundaries.PARISH.str.replace('St Andrew','KSA')
# master_nodes.parish = master_nodes.parish.str.replace('St','St.')

# add parishes to nodes
new_master_nodes = gpd.overlay(master_nodes,boundaries)
# parish col
new_master_nodes['parish'] = new_master_nodes['PARISH']
# map electricity intensities by parish
new_master_nodes['elec_intensity'] = new_master_nodes['parish'].map(ei_dict)
# reindex
new_master_nodes = new_master_nodes[['id', 'asset_type', 'subtype', 'capacity', 'uc_min', 'uc_max', 'uc_avg',
                                     'uc_uom', 'cost_min', 'cost_max', 'cost_avg', 'cost_uom', 'degree',
                                     'population', 'ei', 'ei_uom','parish', 'title', 'source','geometry']]
# save
new_master_nodes.to_file(driver='ESRI Shapefile',filename='../data/spatial/infrasim-network/nodes.shp')
print('done')