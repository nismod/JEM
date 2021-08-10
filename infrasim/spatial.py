import geopandas as gpd
from shapely.geometry import Point
import snkit

from .metainfo import *

def add_graph_topology(nodes,edges,id_attribute='ID',save=False,label=False):
    '''
    Function to add i,j,k notation to edges
    '''
    i_field = metainfo['i_field']
    j_field = metainfo['j_field']
    #find nearest node to the START coordinates of the line -- and return the 'ID' attribute
    edges[i_field] = edges.geometry.apply(lambda geom: snkit.network.nearest(Point(geom.coords[0]), nodes)[id_attribute])
    #find nearest node to the END coordinates of the line -- and return the 'ID' attribute
    edges[j_field] = edges.geometry.apply(lambda geom: snkit.network.nearest(Point(geom.coords[-1]), nodes)[id_attribute])
    #order columns
    edges = edges[ metainfo['edges_header'] + ['geometry'] ]
    #label
    if label==True:
        edges['label'] = '(' + edges[i_field] + ',' + edges[j_field] + ')'
    #save
    if save==True:
        edges.to_file(driver='ESRI Shapefile', filename='edges_processed.shp')
    return edges

def drop_geom(nodes,edges):
    nodes = nodes.drop('geometry',axis=1)
    edges = edges.drop('geometry',axis=1)
    return nodes, edges

def graph_to_csv(nodes,edges,output_dir=''):
    '''
    Function to export shapefiles csv
    '''
    # export
    nodes.to_csv(output_dir+'nodes.csv',index=False)
    edges.to_csv(output_dir+'edges.csv',index=False)
