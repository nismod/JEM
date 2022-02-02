# -*- coding: utf-8 -*-
"""
Created on Wed Oct 20 13:26:12 2021

@author: aqua
"""

import pandas as pd

from .utils import *

class analyse():
    
    def __init__(self,model_run):
        self.nodes      = model_run.nodes
        self.edges      = model_run.edges
        self.flows      = model_run.flows
        self.edge_flows = model_run.results_arcflows
    
    
    def supply_demand_balance(self):
        '''Return dataframe of supply and demand
        '''
        supply_nodes = get_source_nodes(self)
        supply = self.flows[self.flows.Node.isin(supply_nodes)].flow.sum()
        
        demand_nodes = get_sink_nodes(self)
        demand = self.flows[self.flows.Node.isin(demand_nodes)].flow.sum()
        return pd.DataFrame({'supply': [supply], 'demand' : [demand]})
    
    
    def total_demand_shortfall(self):
        '''Return total unmet load
        '''
        if self.edge_flows.loc[self.edge_flows.from_id == 'super_source'] is True:
            return 0
        else:
            return self.edge_flows.loc[self.edge_flows.from_id == 'super_source'].flow.sum()
    
    
    def nodes_with_shortfall(self):
        '''Return dataframe of nodes with shortage
        '''
        idx = self.super_source_flows()
        idx['node'] = idx['to_id']
        idx['shortfall'] = idx['flow']
        return idx[['node','shortfall','timestep']].reset_index(drop=True)
    
    
    def customers_affected(self):
        '''Return total population affected 
        '''
        n = self.nodes_with_shortfall().node.to_list()
        p = self.get_population_at_nodes(nodes=n)
        return p.population.sum().astype('int')
    
    
    def customers_affected_total(self):
        '''Return population affected 
        '''
        n = self.nodes_with_shortfall().node.to_list()
        p = self.get_population_at_nodes(nodes=n)
        p.population = p.population.astype('int')
        return p.reset_index(drop=True)
    
    
    def super_source_flows(self):
        '''Return flows from super_source
        '''
        return self.edge_flows[(self.edge_flows.from_id == 'super_source') & \
                               (self.edge_flows.flow > 0)].copy().reset_index(drop=True)
    
    
    def get_population_at_nodes(self,nodes):
        '''Return population at list of nodes
        '''
        return self.nodes[self.nodes.id.isin(nodes)][['id','population']]