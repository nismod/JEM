'''
    utils.py
        Series of functions to make life a bit easier

    @amanmajid
'''

import os
import networkx as nx
import matplotlib.pyplot as plt

def results_to_graph(results,**kwargs):

    # define graph
    G = nx.DiGraph()

    # define edges
    for i in results.index:
        # add edge if it has flow going through it
        if results.Value.loc[i] > 0:

            G.add_edge(results.Start.loc[i],
                       results.End.loc[i],
                       weight=results.Value.loc[i]+0.2,
                       label="{:.2f}".format(results.Value.loc[i]*100)+'%')

    # position graph in circular layout
    pos = nx.circular_layout(G)

    # get edge attributes
    edge_widths = nx.get_edge_attributes(G, 'weight')
    edge_labels = nx.get_edge_attributes(G, 'label')

    # draw nodes
    nx.draw_networkx_nodes(G,
                           pos,
                           nodelist=G.nodes(),
                           node_size=300,
                           node_color=kwargs.get('edge_color', 'black'),
                           alpha=1)

    # draw edges
    nx.draw_networkx_edges(G,
                           pos,
                           edgelist = edge_widths.keys(),
                           width=list(edge_widths.values()),
                           arrowsize=20,
                           edge_color=kwargs.get('edge_color', 'black'),
                           alpha=1)

    # draw node labels
    nx.draw_networkx_labels(G,
                            pos=pos,
                            labels=dict(zip(G.nodes(),G.nodes())),
                            font_color=kwargs.get('node_font_color', 'black'),
                            font_size=kwargs.get('node_font_size', 10))

    # draw edge labels
    nx.draw_networkx_edge_labels(G,
                                 pos,
                                 edge_labels=edge_labels,
                                 label_pos=0.5,
                                 rot=90,
                                 font_size=kwargs.get('edge_font_size', 10))

    return G


def plot_storage_volume(storage_results,node,**kwargs):
    '''Plot storage volume at a given node
    '''
    v = storage_results[storage_results.Node==node].reset_index(drop=True)
    ax = v.Value.plot(color='blue')
    ax.set_xlabel('Time')
    ax.set_ylabel('Storage Volume')
    ax.set_xlim([kwargs.get("xlim", None)])
    ax.set_ylim([kwargs.get("ylim", None)])
    plt.axhline(y=v.Value.max(), color='gray', linestyle=':')


def plot_inflow_outflow(arcflow_result,node,**kwargs):
    '''Plot nodal inflow and outflows
    '''
    inflow  = arcflow_result[arcflow_result.End==node].groupby(by='timestep').sum().reset_index(drop=True)
    outflow = arcflow_result[arcflow_result.Start==node].groupby(by='timestep').sum().reset_index(drop=True)

    grouped = kwargs.get("grouped", True)

    if grouped==True:
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (5,5)))
        ax.plot(inflow.Value,color='blue',label='Inflow')
        ax.plot(outflow.Value,color='red',label='Outflow')
        ax.set_xlabel('Time')
        ax.set_ylabel('Inflow-Outflow')
        plt.legend(loc='upper right')

    elif grouped==False:
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (5,5)),nrows=2,ncols=1)
        plt.subplot(2,1,1)
        plt.plot(inflow.Value,color='blue',label='Inflow')
        plt.ylabel('Inflow-Outflow')
        plt.legend()
        plt.subplot(2,1,2)
        plt.plot(outflow.Value,color='red',label='Outflow')
        plt.ylabel('Inflow-Outflow')
        plt.legend()
        plt.xlabel('Time')
