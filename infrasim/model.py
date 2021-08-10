'''
    infrasim.jem
        A network flow model for the jamaica's energy system

    @amanmajid
'''

import gurobipy as gp
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import time

from . import utils
from . import spatial
from . import plotting

from .meta import *
from .params import *


class infrasim():


    def __init__(self,nodes,edges,flows,**kwargs):

        #---
        # Read data

        # read shape files of nodes and edges
        if '.shp' in nodes and '.shp' in edges:
            nodes = gpd.read_file(nodes)
            edges = gpd.read_file(edges)
            # drop geometry
            # nodes,edges = spatial.drop_geom(nodes,edges)

        # else read csv files of nodes and edges
        elif '.csv' in nodes and '.csv' in edges:
            nodes = pd.read_csv(nodes)
            edges = pd.read_csv(edges)
        
        # read flow data
        flows = pd.read_csv(flows)

        # restrict timesteps
        timesteps_restriction = kwargs.get("timesteps", None)
        if timesteps_restriction is not None:
            flows = flows.loc[(flows.Timestep >= timesteps_restriction) & \
                              (flows.Timestep <= timesteps_restriction)]

        #---
        # Add super source
        super_source = kwargs.get("super_source", False)
        if super_source==True:
            edges = utils.add_super_source(nodes,edges)

        #---
        # Add super sink
        super_sink = kwargs.get("super_sink", False)
        if super_sink==True:
            edges = utils.add_super_sink(nodes,edges)

        #---
        # Tidy flow data
        flows = utils.tidy(flows)

        #---
        # Create infrasim cache files
        utils.create_dir(path=metainfo['infrasim_cache'])
        spatial.graph_to_csv(nodes,edges,output_dir=metainfo['infrasim_cache'])
        flows.to_csv(metainfo['infrasim_cache']+'flows.csv')

        #---
        # add time indices to edge data
        self.edge_indices   = utils.add_time_to_edges(flows,edges)

        #---
        # Define sets
        self.flows          = flows
        self.edges          = edges
        self.nodes          = nodes
        self.indices        = metainfo['edge_index_variables']
        self.constants      = constants
        self.node_types     = self.nodes.asset_type.unique().tolist()
        self.technologies   = self.nodes.subtype.unique().tolist()
        self.timesteps      = self.flows.Timestep.unique().tolist()

        #---
        # define gurobi model
        model_name          = 'infrasim'
        self.model          = gp.Model(model_name)

        #---
        # define model temporal resolution
        self.temporal_resolution = metainfo['temporal_resolution']


    def build(self):
        '''

        Contents:
        -------

            1. Variables
            2. Objective Function
            3. Generic Constraints

        '''

        from_id_time = time.process_time()

        #======================================================================
        # VARIABLES
        #======================================================================

        #---
        # arcflows
        arc_indicies      = self.edge_indices[self.indices].set_index(keys=self.indices).index.to_list()
        self.arcFlows     = self.model.addVars(arc_indicies,name="arcflow")



        #======================================================================
        # OBJECTIVE FUNCTION
        #======================================================================

        #---
        # Minimise cost of flow
        self.costDict = utils.arc_indicies_as_dict(self,metainfo['cost_column'])

        self.model.setObjectiveN(gp.quicksum(self.arcFlows[i,j,t] * self.costDict[i,j,t]
                                              for i,j,t in self.arcFlows),0,weight=1)



        #======================================================================
        # CONSTRAINTS
        #======================================================================

        #----------------------------------------------------------------------
        # SUPER NODES
        #----------------------------------------------------------------------

        if 'super_source' in self.edges.from_id.unique():
            # constrain
            self.model.addConstrs((
                            self.arcFlows.sum('super_source','*',t)  <= constants['super_source_maximum']
                            for t in self.timesteps),'super_source_supply')

        if 'super_sink' in self.edges.to_id.unique():
            # constrain
            self.model.addConstrs((
                            self.arcFlows.sum('*','super_sink',t)  >= 0
                            for t in self.timesteps),'super_sink_demand')
        
        
        #----------------------------------------------------------------------
        # SUPPLY/DEMAND
        #----------------------------------------------------------------------



        #----------------------------------------------------------------------
        # ARC FLOW BOUNDS
        #----------------------------------------------------------------------

        # Flows must be below upper bounds
        upper_bound = utils.arc_indicies_as_dict(self,metainfo['upper_bound'])
        self.model.addConstrs((self.arcFlows[i,j,t] <= upper_bound[i,j,t]
                               for i,j,t in self.arcFlows),'upper_bound')

        # Flows must be above lower bounds
        lower_bound = utils.arc_indicies_as_dict(self,metainfo['lower_bound'])
        self.model.addConstrs((lower_bound[i,j,t] <= self.arcFlows[i,j,t]
                               for i,j,t in self.arcFlows),'lower_bound')


        #----------------------------------------------------------------------
        # JUNCTIONS
        #----------------------------------------------------------------------

        #---
        # Junction node balance
        if 'junction' in self.node_types:
            junction_nodes = utils.get_node_names(nodes=self.nodes,index_column='asset_type',lookup='junction')

            self.model.addConstrs((
                     self.arcFlows.sum('*',j,t)  == self.arcFlows.sum(j,'*',t)
                            for t in self.timesteps
                            for j in junction_nodes),'junction_balance')
            

        print(time.process_time() - from_id_time, "seconds")
        
        print('------------- MODEL BUILD COMPLETE -------------')






    def run(self,pprint=True,write=True):
        ''' Function to solve GurobiPy model'''
        # write model to LP
        if write==True:
            self.model.write(metainfo['infrasim_cache']+self.model.ModelName+'.lp')
        # set output flag
        if pprint==True:
            self.model.setParam('OutputFlag', 1)
        else:
            self.model.setParam('OutputFlag', 0)
        # optimise
        self.model.optimize()

        # WRITE RESULTS
        utils.create_dir(path=metainfo['outputs_data'])

        if self.model.Status == 2:
            # arcFlows
            arcFlows            = self.model.getAttr('x', self.arcFlows)
            keys                = pd.DataFrame(arcFlows.keys(),columns=['from_id','to_id','Timestep'])
            vals                = pd.DataFrame(arcFlows.items(),columns=['key','Value'])
            results_arcflows    = pd.concat([keys,vals],axis=1)
            results_arcflows    = results_arcflows[['from_id','to_id','Timestep','Value']]
            # write csv
            results_arcflows.to_csv(metainfo['outputs_data']+'results_arcflows.csv',index=False)
            self.results_arcflows = results_arcflows






    def debug(self,output_path=''):
        '''
        Compute model Irreducible Inconsistent Subsystem (IIS) to help deal with infeasibilies
        '''
        self.model.computeIIS()
        self.model.write(metainfo['infrasim_cache']+'model-debug-report.ilp')






    def postprocess(self):
        ''' Post processing of results 
        '''
        print('to do')
