# -*- coding: utf-8 -*-
"""

    create_flow_data.py

        Create a nodal flow file from spatial data

"""

#=======================
# Modules

import geopandas as gpd

# Add local directory to path
import sys
sys.path.append("../../")

# Import local functions
from utils import *



#=======================
# PARAMS

verbose_flag = True



#=======================
# PROCESSING

# read data
network = read_data(path_to_nodes='../data/spatial/nodes_processed.shp')
verbose_print('loaded data',flag=verbose_flag)