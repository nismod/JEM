import geopandas as gpd
import re

# Add local directory to path
import sys
sys.path.append("../../")
# Import infrasim spatial tools
from JEM.infrasim.spatial import get_isolated_graphs
# Import local copy of snkit
from JEM.snkit.snkit.src.snkit.network import *


def verbose_print(msg,flag=True):
    verbose = flag
    if not verbose:
        pass
    else:
        print(msg)


def read_data(with_snkit=True,**kwargs):
    # paths
    path_to_edges = kwargs.get('path_to_edges','../data/spatial/edges.shp')
    path_to_nodes = kwargs.get('path_to_nodes','../data/spatial/nodes.shp')
    # read
    edges = gpd.read_file(path_to_edges)
    nodes = gpd.read_file(path_to_nodes)
    if not with_snkit:
        return nodes,edges
    else:
        return Network(nodes,edges)


def read_processed_data(with_snkit=True,**kwargs):
    # paths
    path_to_edges = kwargs.get('path_to_edges','../data/spatial/edges_processed.shp')
    path_to_nodes = kwargs.get('path_to_nodes','../data/spatial/nodes_processed.shp')
    # read
    edges = gpd.read_file(path_to_edges)
    nodes = gpd.read_file(path_to_nodes)
    if not with_snkit:
        return nodes,edges
    else:
        return Network(nodes,edges)


def save_data(network,**kwargs):
    '''Save processed node and edge data
    '''
    network.nodes.to_file(\
        driver='ESRI Shapefile', filename=kwargs.get('path_to_nodes','../data/spatial/nodes_processed.shp'))
                          
    network.edges.to_file(\
        driver='ESRI Shapefile', filename=kwargs.get('path_to_edges','../data/spatial/edges_processed.shp'))
    

def extract_parish_sample(network,parish_name):
    '''Extract a sample for a given parish
    '''
    #SAMPLE
    network.nodes = network.nodes.loc[nodes.parish.isin(parish_name)].reset_index(drop=True)
    network.edges = network.edges.loc[edges.parish.isin(parish_name)].reset_index(drop=True)
    return network


def coord_rounding(match):
    '''Rounding coordinates
    '''
    return "{:.5f}".format(float(match.group()))
simpledec = re.compile(r"\d*\.\d+")


def add_id_to_nodes(network):
    '''Adds IDs to nodes
    '''
    ids = ['node_' + str(i+1) for i in range(len(network.nodes))]
    network.nodes['id'] = ids
    return network


def add_id_to_edges(network):
    '''Add IDs to edges
    '''
    ids = ['edge_' + str(i+1) for i in range(len(network.edges))]
    network.edges['id'] = ids
    return network


def add_edge_notation(network):
    '''Add i,j notation to edges
    '''
    i_field = 'from_id'
    j_field = 'to_id'
    id_attribute = 'id'
    #find nearest node to the START coordinates of the line -- and return the 'ID' attribute
    network.edges[i_field] = network.edges.geometry.apply(lambda geom: nearest(Point(geom.coords[0]), network.nodes)[id_attribute])
    #find nearest node to the END coordinates of the line -- and return the 'ID' attribute
    network.edges[j_field] = network.edges.geometry.apply(lambda geom: nearest(Point(geom.coords[-1]), network.nodes)[id_attribute])
    return network


def add_edge_nodal_notation(network):
    '''Add from_node,to_node to edge data
    '''
    nodal_keys = network.nodes[['id','asset_type']].set_index('id')['asset_type'].to_dict()
    network.edges['from_type']  = network.edges['from_id'].map(nodal_keys)
    network.edges['to_type']    = network.edges['to_id'].map(nodal_keys)
    return network


def flip(line):
    '''Reverse arc direction
    '''
    return LineString(reversed(line.coords))


def update_notation(network):
    '''Update node and edge notation
    '''
    # drop existing
    try:
        network.edges.drop(['id','from_id','to_id'],axis=1)
        network.nodes.drop(['id'],axis=1)
    except:
        pass
    # update
    network = add_id_to_nodes(network)
    network = add_id_to_edges(network)
    network = add_edge_notation(network)
    network = add_edge_nodal_notation(network)
    return network


def remove_nontype(network):
    '''remove nontype data from nodes and edges
    '''
    network.edges = network.edges.loc[network.edges.is_valid].reset_index(drop=True)
    network.nodes = network.nodes[~network.nodes.geometry.isna()].reset_index(drop=True)
    # update notation
    network = update_notation(network)
    return network


def explode_multipart(network):
    '''explode multilpart linestrings
    '''
    network.edges = network.edges.explode()
    return network


def add_edge_length(network,multiply_factor=1):
    '''Add length to edge data
    '''
    network.edges['length'] = network.edges.geometry.length * multiply_factor
    return network


def remove_duplicates(network):
    '''remove duplicates
    '''
    network.edges = network.edges.drop_duplicates(subset=['from_id', 'to_id'], keep='first').reset_index(drop=True)
    # update notation
    network = update_notation(network)
    return network


def add_limits_to_edges(network,amp_assumption=700):
    '''Add flow limits to edge data
    '''
    network.edges['min'] = 0
    # Volts * Amps = Watts
    network.edges['max'] = network.edges.voltage_kV.astype('int') \
                            * 1000 * amp_assumption * 10 ** -6 # MW
    return network


def add_capacity_to_nodes(network):
    return network


def bidirectional_edges(network):
    ''' Double edges to represent bidirectionality
    '''
    ee = network.edges.copy()
    # reverse ids
    ee['from_id']   = network.edges['to_id']
    ee['to_id']     = network.edges['from_id']
    # reverse geom
    for i in ee.index:
        ee.loc[i,'geometry'] = flip(ee.loc[i].geometry)
    # append
    network.edges = network.edges.append(ee,ignore_index=True)
    # update notation
    network = update_notation(network)
    return network


def add_nodal_degree(network):
    '''Add nodal degree connectivity
    '''
    network.nodes['degree'] = network.nodes.id.apply(lambda x: node_connectivity_degree(x,network=network))
    return network


def remove_sink_to_sink(network):
    '''remove any sink to sink connections (i.e. stranded network components)
    '''
    sink_to_sink = network.edges.loc[\
                        (network.edges.from_type == 'sink') & \
                            (network.edges.to_type== 'sink')].reset_index(drop=True)
    # get nodes and edges to remove
    nodes_to_remove = sink_to_sink.from_id.to_list() + sink_to_sink.to_id.to_list()
    edges_to_remove = sink_to_sink.id.to_list()
    # remove
    ###network.nodes = network.nodes.loc[~network.nodes.id.isin(nodes_to_remove)].reset_index(drop=True)
    network.edges = network.edges.loc[~network.edges.id.isin(edges_to_remove)].reset_index(drop=True)
    # update notation
    network = update_notation(network)
    return network


def remove_stranded_nodes(network):
    '''Removes nodes with connectivity degree = 0
    '''
    idx = network.nodes.loc[(network.nodes.degree == 0) \
                            #& (network.nodes.asset_type == 'sink') \
                            ].index
    # drop
    network.nodes = network.nodes.drop(idx).reset_index(drop=True)
    # update notation
    network = update_notation(network)
    return network


def remove_self_loops(network):
    '''Removes i to i connections
    '''
    network.edges = network.edges[network.edges.from_id != network.edges.to_id].reset_index(drop=True)
    # update notation
    network = update_notation(network)
    return network


def remove_multiline(network):
    '''Get rid of multiline strings
    '''
    # merge multilinestrings
    network.edges.geometry = network.edges.geometry.apply(merge_multilinestring)
    network.edges = network.edges.loc[network.edges.geom_type == 'LineString'].reset_index(drop=True)
    return network


def get_flow_nodes(network):
    '''Return sources and sinks
    '''
    return network.nodes.loc[network.nodes.asset_type.isin(['source','sink'])].copy()
