'''
    utils.py
        Series of functions to make life a bit easier

    @amanmajid
'''

import os
import numpy as np
import pandas as pd
import geopandas as gpd

from . import spatial
from .meta import *
from .params import *


#---
# Conversions
#---

def kwh_to_gwh(v):
    '''Kilowatt hours to Gigawatt hours
    '''
    return v*0.000001


def gwh_to_kwh(v):
    '''Gigawatt hours to Kilowatt hours
    '''
    return v/0.000001


def cmd_to_mld(v):
    '''Cubic meters per day to megalitres per day
    '''
    return v/0.001


def mld_to_cmd(v):
    '''Megalitres per day to cubic meters per day
    '''
    return v*0.001


def lps_to_cmps(v):
    '''Litres per second to cubic meters per second
    '''
    return v*0.001


def seconds_to_hours(v):
    '''Convert seconds to hours
    '''
    return v*3600



#---
# Post-processing
#---

def get_super_source_flows(jem,as_list=True):
        '''Return nodes that are supplied by super_source
        '''
        if as_list is True:
            return list(jem.results_arcflows[ \
                            (jem.results_arcflows.from_id == 'super_source') & \
                            (jem.results_arcflows.flow > 0)].to_id
                        )
        else:
            return jem.results_arcflows[ \
                            (jem.results_arcflows.from_id == 'super_source') & \
                            (jem.results_arcflows.flow > 0)].to_id


def tag_super_source_flows(jem):
    '''Tag nodes that are supplied by super_source
    '''
    n = get_super_source_flows(jem)
    jem.nodes['super_source'] = False
    jem.nodes.loc[jem.nodes.id.isin(n),'super_source'] = True
    return jem


def merge_edges_with_flows(jem):
    '''Merge edge data with results of optimal flows
    '''
    results = jem.results_arcflows.copy()
    edges   = jem.edges.copy()
    if 'timestep' in list(results.columns) and list(edges.columns):
        edges = edges.drop(['timestep'],axis=1)
    #merge
    return edges.merge(results,on=['from_id','to_id'])


def flows_to_shapefile(jem,filename,driver='ESRI Shapefile',timestep=1):
    '''Export optimal flow results to shapefile
    '''
    results = merge_edges_with_flows(jem)
    results.to_file(driver='ESRI Shapefile',filename=filename)


def get_nodal_edges(jem,node):
    return jem.edges.loc[(jem.edges.from_id == node) | \
                         (jem.edges.to_id == node)]


def get_nodal_inflow(jem,node):
    '''Return inflows to a given node
    '''
    return jem.results_arcflows.loc[jem.results_arcflows.to_id == node]


def get_nodal_outflow(jem,node):
    '''Return outflows from a given node
    '''
    return jem.results_arcflows.loc[jem.results_arcflows.from_id == node]


def get_flow_at_node(jem,node):
    '''Return inflows and ouflows at a given node
    '''
    return jem.results_arcflows.loc[ (jem.results_arcflows.from_id == node) | \
                                     (jem.results_arcflows.to_id == node)]


def get_nodal_balance(jem,node):
    '''Return inflow and outflow at a given node
    '''
    inflow  = get_nodal_inflow(jem,node).flow.sum()
    outflow = get_nodal_outflow(jem,node).flow.sum()
    delta   = outflow - inflow
    if delta == 0:
        balance = 'balanced'
    elif delta > 0:
        balance = 'excess'
    elif delta < 0:
        balance = 'shortage'
    return {'inflow' : inflow, 'outflow' : outflow, 'mass_balance' : balance}


def estimate_edge_capacity(jem,cap_name='cap_estimate',rounding=False):
    '''Estimate edge capacity (W) from flow data
    '''
    flow_results = merge_edges_with_flows(jem)
    flow_results[cap_name] = flow_results.flow.divide(24) # Watts
    if not rounding:
        pass
    else:
        flow_results[cap_name] = flow_results[cap_name].apply(lambda x:roundup(x))
    return flow_results[['id',cap_name]]


def roundup(x):
    return x if x % 100 == 0 else x + 100 - x % 100



#---
# Pre-processing (messy code...)
#---

def create_dir(path):
    ''' Create dir if it doesn't exist
    '''
    if not os.path.exists(path):
        os.makedirs(path)

def tidy(flows):
    ''' Convert supply/demand data to tidy format
    '''
    flows['timestep'] = [i for i in range(1,len(flows)+1)]
    id_vars = metainfo['flow_header'] + ['timestep']
    tidy = flows.melt(id_vars=id_vars,var_name='Node',value_name='flow')
    return tidy


def map_timesteps_to_date(flows,mappable):
    ''' Function to map dates to timesteps
    '''
    # get time reference table
    id_vars = metainfo['flow_header'] + ['timestep']
    time_ref = flows[id_vars].groupby(by='timestep').max().reset_index()
    # perform merge
    mapped = pd.merge(mappable,time_ref,on='timestep',how='right')
    return mapped


def add_time_to_edges(flows,edges):
    ''' Function to add time indices to edge data
    '''
    # Number of timesteps
    timesteps = flows.timestep.max()
    # add time
    edges['timestep'] = 1
    #repeat for each timestep
    new_edges = edges.append( [edges]*(timesteps-1) )
    #create time indices in loop
    tt = []
    for i in range(0,timesteps):
        t = edges.timestep.to_numpy() + i
        tt.append(t)
    tt = np.concatenate(tt,axis=0)
    #add time to pandas datafram
    new_edges['timestep'] = tt
    # reset index
    new_edges = new_edges.reset_index(drop=True)
    # add dates
    new_edges = map_timesteps_to_date(flows,new_edges)
    # reorder
    col_order = metainfo['edges_header'] + ['timestep'] + metainfo['flow_header']
    new_edges = new_edges[col_order]
    return new_edges


def arc_indicies_as_dict(self,var_name):
    ''' Function to convert edge indices dataframe to dict
    '''
    asDict = self.edge_indices[self.indices+[var_name]].set_index(keys=self.indices)[var_name].to_dict()
    return asDict


def flows_as_dict(flows):
    ''' Convert flows from csv to dict
    '''
    flows_dict = flows[['Node','timestep','flow']]
    flows_dict = flows_dict.set_index(keys=['Node','timestep']).to_dict()['flow']
    return flows_dict


def add_super_source(nodes,edges):
    ''' Add super source to edges
    '''
    
    new_edges = []
    
    tmp_edges = pd.DataFrame({'from_id'     : 'super_source',
                              'to_id'       : nodes.id.unique(),
                              'length'      : constants['super_source_maximum'],
                              'min'         : 0,
                              'max'         : constants['super_source_maximum']})
    
    new_edges.append(tmp_edges)
    
    new_edges = pd.concat(new_edges,ignore_index=True)
    
    return edges.append(new_edges, ignore_index=True)


def add_super_sink(nodes,edges):
    ''' Add super sinks to edges
    '''
    new_edges = []

    tmp_edges = pd.DataFrame({'from_id'     : nodes.id.unique(),
                              'to_id'       : 'super_sink',
                              'length'      : constants['super_source_maximum'],
                              'min'         : 0,
                              'max'         : constants['super_source_maximum']})
    
    new_edges.append(tmp_edges)
    
    new_edges = pd.concat(new_edges,ignore_index=True)
    
    return edges.append(new_edges, ignore_index=True)


def normalise_column(df_column):
    normalised_column = (df_column-df_column.min()) / (df_column.max()-df_column.min())
    return normalised_column



#---
# Look ups
#---

def get_nodes(nodes,index_column,lookup,index_column2=None,lookup2=None,index_column3=None,lookup3=None):
    ''' Get nodes of particular type and sector '''
    if index_column2 is not None and index_column3 is not None:
        idx_nodes = nodes.loc[(nodes[index_column]==lookup) & \
                              (nodes[index_column2]==lookup2) & \
                              (nodes[index_column3]==lookup3)]
    elif index_column2 is not None:
        idx_nodes = nodes.loc[(nodes[index_column]==lookup) & \
                              (nodes[index_column2]==lookup2)]
    else:
        idx_nodes = nodes.loc[(nodes[index_column]==lookup)]
    return idx_nodes


def get_node_names(nodes,index_column,lookup,index_column2=None,lookup2=None,index_column3=None,lookup3=None):
    ''' Get nodes of particular type and sector '''
    if index_column2 is not None and index_column3 is not None:
        idx_nodes = nodes.loc[(nodes[index_column]==lookup) & \
                              (nodes[index_column2]==lookup2) & \
                              (nodes[index_column3]==lookup3)].id.to_list()
    elif index_column2 is not None:
        idx_nodes = nodes.loc[(nodes[index_column]==lookup) & \
                              (nodes[index_column2]==lookup2)].id.to_list()
    else:
        idx_nodes = nodes.loc[(nodes[index_column]==lookup)].id.to_list()
    return idx_nodes


def get_flow_at_nodes(flows,list_of_nodes):
    ''' Get flows of specific nodes
    '''
    idx_flows = flows.loc[flows.Node.isin(list_of_nodes)].reset_index(drop=True)
    return idx_flows
