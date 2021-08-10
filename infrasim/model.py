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
            # add topology to edge data
            edges = spatial.add_graph_topology(nodes,edges,id_attribute='Name')
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
            flows = flows.loc[(flows.Timestep >= timesteps_restriction[0]) & \
                              (flows.Timestep <= timesteps_restriction[1])]

        #---
        # Add super source
        super_source = kwargs.get("super_source", False)
        if super_source==True:
            edges = utils.add_super_source(nodes,edges,commodities=edges.Commodity.unique())

        #---
        # Add super sink
        super_sink = kwargs.get("super_sink", False)
        if super_sink==True:
            edges = utils.add_super_sink(nodes,edges,commodities=edges.Commodity.unique())

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
        self.commodities    = self.edges.Commodity.unique().tolist()
        self.node_types     = self.nodes.Type.unique().tolist()
        self.technologies   = self.nodes.Subtype.unique().tolist()
        self.functions      = self.nodes.Function.unique().tolist()
        self.timesteps      = self.flows.Timestep.unique().tolist()
        self.days           = self.flows.Day.unique().tolist()
        self.months         = self.flows.Month.unique().tolist()
        self.years          = self.flows.Year.unique().tolist()

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

        start_time = time.clock()

        #======================================================================
        # VARIABLES
        #======================================================================

        #---
        # arcflows
        arc_indicies      = self.edge_indices[self.indices].set_index(keys=self.indices).index.to_list()
        self.arcFlows     = self.model.addVars(arc_indicies,name="arcflow")

        #---
        # storage volumes
        storage_nodes         = utils.get_nodes(nodes=self.nodes,index_column='Type',lookup='storage')

        storage_indices       = [(n, storage_nodes.loc[storage_nodes.Name==n,'Commodity'].values[0], t)
                                 for n in storage_nodes.Name
                                 for t in self.timesteps]

        self.storage_volume   = self.model.addVars(storage_indices,lb=0,name="storage_volume")


        #======================================================================
        # OBJECTIVE FUNCTION
        #======================================================================

        #---
        # Minimise cost of flow
        self.costDict = utils.arc_indicies_as_dict(self,metainfo['cost_column'])

        self.model.setObjectiveN(gp.quicksum(self.arcFlows[i,j,k,t] * self.costDict[i,j,k,t]
                                              for i,j,k,t in self.arcFlows),0,weight=1)



        #======================================================================
        # CONSTRAINTS
        #======================================================================

        #----------------------------------------------------------------------
        # SUPER NODES
        #----------------------------------------------------------------------

        if 'super_source' in self.edges.Start.unique():
            # constrain
            self.model.addConstrs((
                            self.arcFlows.sum('super_source','*',k,t)  <= constants['super_source_maximum']
                            for t in self.timesteps
                            for k in self.commodities),'super_source_supply')

        if 'super_sink' in self.edges.End.unique():
            # constrain
            self.model.addConstrs((
                            self.arcFlows.sum('*','super_sink',k,t)  >= 0
                            for t in self.timesteps
                            for k in self.commodities),'super_sink_demand')

        #----------------------------------------------------------------------
        # ARC FLOW BOUNDS
        #----------------------------------------------------------------------

        # Flows must be below upper bounds
        upper_bound = utils.arc_indicies_as_dict(self,metainfo['upper_bound'])
        self.model.addConstrs((self.arcFlows[i,j,k,t] <= upper_bound[i,j,k,t]
                               for i,j,k,t in self.arcFlows),'upper_bound')

        # Flows must be above lower bounds
        lower_bound = utils.arc_indicies_as_dict(self,metainfo['lower_bound'])
        self.model.addConstrs((lower_bound[i,j,k,t] <= self.arcFlows[i,j,k,t]
                               for i,j,k,t in self.arcFlows),'lower_bound')

        #----------------------------------------------------------------------
        # WATER SUPPLY
        #----------------------------------------------------------------------

        #---
        # Supply from water source nodes
        if 'water' in self.commodities:
            # get water supply nodes
            water_nodes = utils.get_node_names(nodes=self.nodes,
                                               index_column='Type',lookup='source',
                                               index_column2='Nodal_Flow',lookup2='True',
                                               index_column3='Commodity',lookup3='water')

            # get flow at water supply nodes
            water_flows  = utils.get_flow_at_nodes(flows=self.flows,list_of_nodes=water_nodes)
            supply_dict  = utils.flows_as_dict(flows=water_flows)

            # constrain
            self.model.addConstrs((
                            self.arcFlows.sum(i,'*','water',t)  <= supply_dict[i,t]
                            for t in self.timesteps
                            for i in water_nodes),'water_supply')

        #---
        # Demand at sink nodes
        if 'water' in self.commodities:
            # get water demand nodes
            water_nodes = utils.get_node_names(nodes=self.nodes,
                                               index_column='Type',lookup='sink',
                                               index_column2='Nodal_Flow',lookup2='True',
                                               index_column3='Commodity',lookup3='water')

            # get flow at water supply nodes
            water_flows  = utils.get_flow_at_nodes(flows=self.flows,list_of_nodes=water_nodes)
            demand_dict  = utils.flows_as_dict(flows=water_flows)

            # constrain
            self.model.addConstrs((
                            self.arcFlows.sum('*',j,'water',t)  == demand_dict[j,t]
                            for t in self.timesteps
                            for j in water_nodes),'water_demand')


        #----------------------------------------------------------------------
        # JUNCTIONS
        #----------------------------------------------------------------------

        #---
        # Junction node balance
        if 'junction' in self.node_types:
            junction_nodes = utils.get_node_names(nodes=self.nodes,index_column='Type',lookup='junction')

            for k in self.commodities:
                self.model.addConstrs((
                         self.arcFlows.sum('*',j,k,t)  == self.arcFlows.sum(j,'*',k,t)
                                for t in self.timesteps
                                for j in junction_nodes),'junction_balance')

        print(time.clock() - start_time, "seconds")
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
            keys                = pd.DataFrame(arcFlows.keys(),columns=['Start','End','Commodity','Timestep'])
            vals                = pd.DataFrame(arcFlows.items(),columns=['key','Value'])
            results_arcflows    = pd.concat([keys,vals],axis=1)
            results_arcflows    = results_arcflows[['Start','End','Commodity','Timestep','Value']]
            # write csv
            results_arcflows.to_csv(metainfo['outputs_data']+'results_arcflows.csv',index=False)
            self.results_arcflows = results_arcflows

            # storageVolumes
            storage_volumes              = self.model.getAttr('x', self.storage_volume)
            keys                         = pd.DataFrame(storage_volumes.keys(),columns=['Node','Commodity','Timestep'])
            vals                         = pd.DataFrame(storage_volumes.items(),columns=['key','Value'])
            results_storage_volumes      = pd.concat([keys,vals],axis=1)
            results_storage_volumes      = results_storage_volumes[['Node','Commodity','Timestep','Value']]
            self.results_storage_volumes = results_storage_volumes
            # write csv
            results_storage_volumes.to_csv(metainfo['outputs_data']+'results_storage_volumes.csv',index=False)






    def debug(self,output_path=''):
        '''
        Compute model Irreducible Inconsistent Subsystem (IIS) to help deal with infeasibilies
        '''
        self.model.computeIIS()
        self.model.write(metainfo['infrasim_cache']+'model-debug-report.ilp')






    def postprocess(self):
        ''' Post processing of results '''

        utils.create_dir(path=metainfo['outputs_figures'])

        #----------------------------------------------------------------------
        # GRAPH ANALYSIS
        #----------------------------------------------------------------------

        #---
        # Arc utilisation
        for k in self.commodities:
            plt.figure(figsize=(10,8))
            w = self.results_arcflows.loc[self.results_arcflows.Commodity==k].reset_index(drop=True)
            w = w.groupby(by=['Start','End']).sum().reset_index()
            w.Value = w.Value / w.Value.sum()

            if k=='water':
                edge_color='blue'
            elif k=='electricity':
                edge_color='red'
            else:
                edge_color='black'

            G = plotting.results_to_graph(w,edge_color=edge_color)
            plt.savefig(metainfo['outputs_figures']+'arc_utilisation_'+k+'.pdf')
