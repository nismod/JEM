from .utils import get_source_nodes, get_sink_nodes

class statistics:

    def __init__(self, model_run):
        self.nodes = model_run.nodes
        self.edges = model_run.edges
        self.flows = model_run.flows
        self.edge_flows = model_run.results_arcflows

    def supply_demand_balance(self):
        """Return dataframe of supply and demand"""
        supply_nodes = get_source_nodes(self)
        supply = self.flows[self.flows.node.isin(supply_nodes)].flow.sum()

        demand_nodes = get_sink_nodes(self)
        demand = self.flows[self.flows.node.isin(demand_nodes)].flow.sum()
        return pd.DataFrame({"supply": [supply], "demand": [demand]})

    def total_demand_shortfall(self):
        """Return total unmet load"""
        if self.edge_flows.loc[self.edge_flows.from_id == "super_source"] is True:
            return 0
        else:
            return self.edge_flows.loc[
                self.edge_flows.from_id == "super_source"
            ].flow.sum()

    def nodes_with_shortfall(self):
        """Return dataframe of nodes with shortage"""
        idx = self.super_source_flows()
        idx["node"] = idx["to_id"]
        idx["shortfall"] = idx["flow"]
        return idx[["node", "shortfall", "timestep"]].reset_index(drop=True)

    def customers_affected(self):
        """Return total population affected"""
        n = self.nodes_with_shortfall().node.to_list()
        p = self.get_population_at_nodes(nodes=n)
        return p.population.sum().astype("int")

    def customers_affected_total(self):
        """Return population affected"""
        n = self.nodes_with_shortfall().node.to_list()
        p = self.get_population_at_nodes(nodes=n)
        p.population = p.population.astype("int")
        return p.reset_index(drop=True)

    def super_source_flows(self):
        """Return flows from super_source"""
        return (
            self.edge_flows[
                (self.edge_flows.from_id == "super_source") & (self.edge_flows.flow > 0)
            ]
            .copy()
            .reset_index(drop=True)
        )

    def get_population_at_nodes(self, nodes, col_id=None):
        """Return population for list of nodes"""
        if not col_id:
            return self.nodes[self.nodes.id.isin(nodes)][
                ["id", "population"]
            ].reset_index(drop=True)
        else:
            population = self.nodes[self.nodes.id.isin(nodes)][["id", "population"]]
            population[col_id] = population["id"]
        return population[[col_id, "population"]].reset_index(drop=True)

    def get_demand_at_nodes(self, nodes, col_id=None):
        """Return demand for list of nodes"""
        demand = self.flows[self.flows.node.isin(nodes)][["node", "flow"]]
        demand["demand"] = demand["flow"]
        if not col_id:
            return demand[["node", "demand"]].reset_index(drop=True)
        else:
            demand[col_id] = demand["node"]
            return demand[[col_id, "demand"]].reset_index(drop=True)
