# -*- coding: utf-8 -*-
"""
Created on Wed Oct 20 12:16:17 2021

@author: aqua
"""
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


plt.style.use("ggplot")

# --------------------------------------------
# READ RESULTS

# ---
# Damages

node_path = "../data/risk-results/direct_damages_summary/elec/"

f1 = "electricity_network_v1.0_nodes_EAD_without_confidence_value.csv"
f2 = "electricity_network_v1.0_edges_EAD_without_confidence_value.csv"


d1 = pd.read_csv(node_path + f1)
d2 = pd.read_csv(node_path + f2)


d1.loc[d1.rcp == "baseline", "rcp"] = 0
d2.loc[d2.rcp == "baseline", "rcp"] = 0


d1.rcp = d1.rcp.astype("float32")
d2.rcp = d2.rcp.astype("float32")

# ---
# Node,edge data

path_to_nodes = "../data/spatial/infrasim-network/version_1.0/nodes.shp"
path_to_edges = "../data/spatial/infrasim-network/version_1.0/edges.shp"

nodes = gpd.read_file(path_to_nodes)
edges = gpd.read_file(path_to_edges)


# ------------------------
# PLOT 1
#   ecdf of damages by scenario

f, ax = plt.subplots(nrows=1, ncols=2, figsize=(10, 5))

sns.ecdfplot(
    data=d1,
    x="EAD_undefended_median",
    hue="rcp",
    linewidth=2,
    palette=sns.color_palette("Set2", 3),
    ax=ax[0],
)

ax[0].set_xlim([5, 30])
ax[0].set_xlabel("Median EAD \n [$/MW]")
ax[0].set_ylabel("P(x)")

ax[0].legend([8.5, 4.5, "Baseline"], title="RCP")
# ax[0].set_title('Nodes',loc='left',fontweight='bold')


sns.ecdfplot(
    data=d2,
    x="EAD_undefended_median",
    hue="rcp",
    linewidth=2,
    palette=sns.color_palette("Set2", 3),
    ax=ax[1],
)

ax[1].set_xlim([0, 50])
ax[1].set_xlabel("Median EAD Per Node \n [$/MW]")
ax[1].set_ylabel("P(x)")

# ax[1].legend([8.5,4.5,'Baseline'],title='RCP')
ax[1].set_title("Lines", loc="left", fontweight="bold")

f.savefig("../outputs/figures/ecdf-ead-by-rcp.pdf", bbox_inches="tight")


# ------------------------
# PLOT 2
#   Boxplot of damage by asset and hazard type

# merge node data
d1 = d1.merge(nodes, on="id", how="left")
d1 = d1[
    [
        "id",
        "exposure_unit",
        "damage_cost_unit",
        "hazard",
        "rcp",
        "epoch",
        "EAD_undefended_mean",
        "EAD_undefended_min",
        "EAD_undefended_max",
        "EAD_undefended_median",
        "EAD_undefended_q5",
        "EAD_undefended_q95",
        "subtype",
        "parish",
    ]
]

d2 = d2.merge(edges, on="id", how="left")
d2 = d2[
    [
        "id",
        "exposure_unit",
        "damage_cost_unit",
        "hazard",
        "rcp",
        "epoch",
        "EAD_undefended_mean",
        "EAD_undefended_min",
        "EAD_undefended_max",
        "EAD_undefended_median",
        "EAD_undefended_q5",
        "EAD_undefended_q95",
        "asset_type",
        "parish",
    ]
]

d2["subtype"] = d2["asset_type"]
d2 = d2.drop("asset_type", axis=1)

combined = d1.append(d2, ignore_index=True)

# change naming
combined.loc[combined.hazard == "surface", "hazard"] = "Pluvial"
combined.loc[combined.hazard == "fluvial", "hazard"] = "Fluvial"
combined.loc[combined.hazard == "cyclone", "hazard"] = "Cyclone"
combined.loc[combined.subtype == "pole", "subtype"] = "Pole"
combined.loc[combined.subtype == "substation", "subtype"] = "Substation"
combined.loc[combined.subtype == "gas", "subtype"] = "Gas Plant"
combined.loc[combined.subtype == "diesel", "subtype"] = "Diesel Plant"
combined.loc[combined.subtype == "High Voltage", "subtype"] = "Transmission Line"
combined.loc[combined.subtype == "Low Voltage", "subtype"] = "Distribution Line"


# boxplot
def boxy(x, lims, ax):

    sns.boxplot(
        x="subtype",
        y="EAD_undefended_median",
        hue="hazard",
        data=combined[combined.subtype == x],
        palette=sns.color_palette("Set2", 3),
        width=0.3,
        fliersize=0,
        ax=ax,
    )

    ax.set_ylim(lims)
    ax.set_ylabel("")
    ax.set_xlabel("")


f, ax = plt.subplots(nrows=2, ncols=3, figsize=(15, 10))

boxy(x="Pole", lims=[-2, 30], ax=ax[0, 0])
boxy(x="Substation", lims=[-2, 30], ax=ax[0, 1])
boxy(x="Distribution Line", lims=[-2, 30], ax=ax[0, 2])
boxy(x="Transmission Line", lims=[-30, 500], ax=ax[1, 0])
boxy(x="Gas Plant", lims=[0, 120000], ax=ax[1, 1])
boxy(x="Diesel Plant", lims=[0, 100000], ax=ax[1, 2])

f.savefig("../outputs/figures/boxplot-damage-by-asset.pdf", bbox_inches="tight")
