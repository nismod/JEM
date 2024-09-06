"""
    infrasim.jem
        A network flow model for the jamaica's energy system

    @amanmajid
"""

import time

import geopandas as gpd
import gurobipy as gp
import pandas as pd

from . import utils
from . import spatial

from .meta import metainfo
from .params import constants


class jem:

    def __init__(self, nodes, edges, flows, write=False, **kwargs):

        # Read data
        if not isinstance(nodes, pd.DataFrame):
            if ".shp" in nodes:
                nodes = gpd.read_file(nodes)
            elif ".csv" in nodes:
                nodes = pd.read_csv(nodes)
            elif ".gpkg" in nodes:
                nodes = gpd.read_file(nodes, layer="nodes")
            else:
                assert False, "Unrecognised file extension"
        else:
            nodes = nodes.copy()

        if not isinstance(edges, pd.DataFrame):
            if ".shp" in edges:
                edges = gpd.read_file(edges)
            elif ".csv" in edges:
                edges = pd.read_csv(edges)
            elif ".gpkg" in edges:
                edges = gpd.read_file(edges, layer="edges")
            else:
                assert False, "Unrecognised file extension"
        else:
            edges = edges.copy()

        if not isinstance(flows, pd.DataFrame):
            flows = pd.read_csv(flows)
        else:
            flows = flows.copy()

        # restrict timesteps
        timesteps_restriction = kwargs.get("timesteps", None)
        if timesteps_restriction is not None:
            flows = flows.loc[
                (flows.timestep >= timesteps_restriction)
                & (flows.timestep <= timesteps_restriction)
            ]

        # ---
        # Add super source
        super_source = kwargs.get("super_source", False)
        if super_source:
            edges = utils.add_super_source(nodes, edges)

        # ---
        # Add super sink
        super_sink = kwargs.get("super_sink", False)
        if super_sink:
            edges = utils.add_super_sink(nodes, edges)

        # ---
        # Tidy flow data
        flows = utils.tidy(flows)
        # flows.flow = flows.flow.abs()

        # ---
        # Create infrasim cache files
        if write:
            utils.create_dir(path=metainfo["infrasim_cache"])
            spatial.graph_to_csv(nodes, edges, output_dir=metainfo["infrasim_cache"])
            flows.to_csv(metainfo["infrasim_cache"] + "flows.csv")

        # ---
        # add time indices to edge data
        self.edge_indices = utils.add_time_to_edges(flows, edges)

        # ---
        # Define sets
        self.flows = flows
        self.edges = edges
        self.nodes = nodes
        self.indices = metainfo["edge_index_variables"]
        self.constants = constants
        self.node_types = self.nodes.asset_type.unique().tolist()
        self.technologies = self.nodes.subtype.unique().tolist()
        self.timesteps = self.flows.timestep.unique().tolist()

        # ---
        # define gurobi model
        model_name = "infrasim"
        self.model = gp.Model(model_name)

        # ---
        # define model temporal resolution
        self.temporal_resolution = metainfo["temporal_resolution"]

        # ---
        # print out
        self._print = kwargs.get("print_to_console", False)

        if self._print is False:
            self.model.Params.LogToConsole = 0

        # ---
        # attackable nodes
        self.nodes_to_attack = kwargs.get("nodes_to_attack", None)
        self.edges_to_attack = kwargs.get("edges_to_attack", None)

        # zero edges associated with attackable nodes
        if not self.nodes_to_attack:
            pass
        else:
            self.edge_indices.loc[
                self.edge_indices.from_id.isin(self.nodes_to_attack), "max"
            ] = 0
            self.edge_indices.loc[
                self.edge_indices.to_id.isin(self.nodes_to_attack), "max"
            ] = 0

        # zero attackable edges
        if not self.edges_to_attack:
            pass
        else:
            self.edge_indices.loc[
                self.edge_indices.id.isin(self.edges_to_attack), "max"
            ] = 0

    def build(self, **kwargs):
        """

        Contents:
        -------

            1. Variables
            2. Objective Function
            3. Generic Constraints

        """

        from_id_time = time.process_time()

        # ======================================================================
        # VARIABLES
        # ======================================================================

        # ---
        # arcflows
        self.arc_indicies = set(
            self.edge_indices[self.indices].set_index(keys=self.indices).index.to_list()
        )
        self.arcFlows = self.model.addVars(self.arc_indicies, name="arcflow")

        # ======================================================================
        # OBJECTIVE FUNCTION
        # ======================================================================

        # ---
        # Minimise cost of flow
        self.costDict = utils.arc_indicies_as_dict(self, metainfo["cost_column"])

        self.model.setObjectiveN(
            gp.quicksum(
                self.arcFlows[i, j, t] * self.costDict[i, j, t]
                for i, j, t in self.arcFlows
            ),
            0,
            weight=1,
        )

        # ======================================================================
        # CONSTRAINTS
        # ======================================================================

        # ---
        # SUPER SOURCE

        if "super_source" in self.edges.from_id.unique():
            # constrain
            self.model.addConstrs(
                (
                    self.arcFlows.sum("super_source", "*", t)
                    <= constants["super_source_maximum"]
                    for t in self.timesteps
                ),
                "super_source_supply",
            )

        # ---
        # SUPER SINK

        if "super_sink" in self.edges.to_id.unique():
            # constrain
            self.model.addConstrs(
                (self.arcFlows.sum("*", "super_sink", t) >= 0 for t in self.timesteps),
                "super_sink_demand",
            )

        # ---
        # SUPPLY

        # get source nodes
        sources = utils.get_node_names(
            nodes=self.nodes, index_column="asset_type", lookup="source"
        )

        # get flow at supply nodes
        flow_dict = utils.get_flow_at_nodes(flows=self.flows, list_of_nodes=sources)
        flow_dict = utils.flows_as_dict(flows=flow_dict)

        # constrain: supply from source nodes
        self.model.addConstrs(
            (
                self.arcFlows.sum(i, "*", t) <= flow_dict[i, t]
                for t in self.timesteps
                for i in sources
            ),
            "supply",
        )

        # constrain: demand at source nodes
        self.model.addConstrs(
            (
                self.arcFlows.sum("*", i, t) == 0
                for t in self.timesteps
                for i in sources
            ),
            "supply",
        )

        # ---
        # DEMAND

        # get sink nodes
        sinks = utils.get_node_names(
            nodes=self.nodes, index_column="asset_type", lookup="sink"
        )

        # get flow at supply nodes
        flow_dict = utils.get_flow_at_nodes(flows=self.flows, list_of_nodes=sinks)
        flow_dict = utils.flows_as_dict(flows=flow_dict)

        # constrain
        self.model.addConstrs(
            (
                self.arcFlows.sum("*", i, t) == flow_dict[i, t]
                for t in self.timesteps
                for i in sinks
            ),
            "demand",
        )

        # ---
        # CONSERVATION OF ENERGY

        # constrain: conservation of energy
        self.model.addConstrs(
            (
                self.arcFlows.sum("*", j, t) - flow_dict[j, t]
                == self.arcFlows.sum(j, "*", t)
                for t in self.timesteps
                for j in sinks
            ),
            "cons_of_energy",
        )

        # ---
        # JUNCTION BALANCE
        junction_nodes = utils.get_node_names(
            nodes=self.nodes, index_column="asset_type", lookup="junction"
        )

        # constrain: flow between junction nodes
        self.model.addConstrs(
            (
                self.arcFlows.sum("*", j, t) == self.arcFlows.sum(j, "*", t)
                for t in self.timesteps
                for j in junction_nodes
            ),
            "junc_bal",
        )

        # ---
        # UPPER FLOW BOUND

        # Flows must be below upper bounds
        upper_bound = utils.arc_indicies_as_dict(self, metainfo["upper_bound"])
        self.model.addConstrs(
            (
                self.arcFlows[i, j, t]
                <= upper_bound[i, j, t]
                * 10**12  # TODO check if this is relaxing all upper bounds?
                for i, j, t in self.arcFlows
            ),
            "upper_bound",
        )

        # ---
        # LOWER FLOW BOUND

        # Flows must be above lower bounds
        lower_bound = utils.arc_indicies_as_dict(self, metainfo["lower_bound"])
        self.model.addConstrs(
            (
                lower_bound[i, j, t] <= self.arcFlows[i, j, t]
                for i, j, t in self.arcFlows
            ),
            "lower_bound",
        )

        if self._print:
            print(time.process_time() - from_id_time, "seconds")
            print("------------- MODEL BUILD COMPLETE -------------")

    def optimise(self, write=False, **kwargs):
        """Function to solve GurobiPy model"""
        # write model to LP
        if write:
            self.model.write(metainfo["infrasim_cache"] + self.model.ModelName + ".lp")
        # set output flag
        if kwargs.get("print_to_console", False):
            self.model.Params.LogToConsole = 1
            self.model.setParam("OutputFlag", 1)
        else:
            self.model.setParam("OutputFlag", 0)
        # optimise
        self.model.optimize()

        # WRITE RESULTS
        if write:
            utils.create_dir(path=metainfo["outputs_data"])

        if self.model.Status == 2:
            # arcFlows
            arcFlows = self.model.getAttr("x", self.arcFlows)
            keys = pd.DataFrame(
                arcFlows.keys(), columns=["from_id", "to_id", "timestep"]
            )
            vals = pd.DataFrame(arcFlows.items(), columns=["key", "flow"])
            results_arcflows = pd.concat([keys, vals], axis=1)
            results_arcflows = results_arcflows[
                ["from_id", "to_id", "timestep", "flow"]
            ]
            if write:
                # write csv
                results_arcflows.to_csv(
                    metainfo["outputs_data"] + "results_arcflows.csv", index=False
                )
            self.results_arcflows = results_arcflows

    def debug(self):
        """
        Compute model Irreducible Inconsistent Subsystem (IIS) to help deal with infeasibilies
        """
        self.model.computeIIS()
        self.model.write(metainfo["infrasim_cache"] + "model-debug-report.ilp")
