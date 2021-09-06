import geopandas as gpd
from shapely.geometry import Point
import snkit
import networkx as nx

from .meta import *


def add_graph_topology(nodes,edges,id_attribute='ID',save=False,label=False):
    ''' Add i,j,k notation to edges
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
    ''' Drop gemoetry from network data
    '''
    nodes = nodes.drop('geometry',axis=1)
    edges = edges.drop('geometry',axis=1)
    return nodes, edges



def graph_to_csv(nodes,edges,output_dir=''):
    ''' Export shapefiles csv
    '''
    
    # export
    nodes.to_csv(output_dir+'nodes.csv',index=False)
    edges.to_csv(output_dir+'edges.csv',index=False)


def to_nx(nodes,edges):
    ''' Export geopandas network to networkx
    '''
    
    # init graph
    G = nx.Graph()

    # add nodes
    G.add_nodes_from(nodes.id.to_list())
    
    # create list of weighted edges
    edges_as_list = [(edges.loc[i].from_id, 
                      edges.loc[i].to_id, 
                      edges.loc[i].length_km) for i in edges.index]
    
    # add edges to graph
    G.add_weighted_edges_from(edges_as_list)
    return G
    

def get_isolated_graphs(nodes,edges):
    ''' Find subgraphs within network and tag edges by graph
    '''
    # define as nx
    G = to_nx(nodes,edges)
    
    # get connected_components
    connected_parts = sorted(nx.connected_components(G), key = len, reverse=True)
    
    # tag each individual network
    count = 1
    edges['nx_part'] = 0
    
    for part in connected_parts:
        edges.loc[ (edges.from_id.isin(list(part))) | \
                   (edges.to_id.isin(list(part))), 'nx_part' ] = count
            
        # adjust counter
        count = count + 1
        
    return nodes,edges