# -*- coding: utf-8 -*-
"""
Created on Sat Sep 18 18:04:23 2021

@author: aqua
"""

#=======================
# Modules
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import pandas as pd
import geopandas as gpd

# Add local directory to path
import sys
sys.path.append("../../")

from utils import *


def process_raw_consumption_data(path):
    '''Process raw consumption data from JPS
    '''
    elec_data  = pd.read_csv(path)
    elec_data  = elec_data[['PARISH','Year','PARISH LOAD']]
    # pivot data
    elec_data  = elec_data.pivot(index='PARISH',columns='Year')
    elec_data.columns = [str(i[1]) for i in elec_data.columns.values]
    elec_data = elec_data.reset_index()
    # convert str to data
    try:
        for col in ['2014', '2015', '2016', '2017', '2018', '2019', '2020',]:
            elec_data[col] = elec_data[col].str.strip().str.replace(',','')
            elec_data[col] = elec_data[col].astype(float)
    except:
        pass
    # rename parish col
    elec_data['Parish'] = elec_data['PARISH']
    elec_data = elec_data.drop(['PARISH'],axis=1)
    # rename parish names
    elec_data.Parish = elec_data.Parish.str.replace('Portmore', 'St. Catherine')
    elec_data.Parish = elec_data.Parish.str.replace('KSAN', 'St. Andrew')
    elec_data.Parish = elec_data.Parish.str.replace('KSAS', 'Kingston')
    # group KSAN and KSAS data
    elec_data = elec_data.groupby(by=['Parish']).sum().reset_index()
    # get latest year
    elec_data = elec_data[['Parish',max(elec_data.columns.drop('Parish'))]]
    return elec_data


def append_energy_data_to_boundaries(boundaries,elec_data):
    '''Combine energy data and admin boundaries
    '''
    elec_dict = elec_data.set_index('Parish')['2020'].to_dict()
    boundaries['consumption'] = boundaries['PARISH'].map(elec_dict)
    boundaries['ei'] = boundaries.consumption / boundaries.POP2001
    boundaries['ei_uom'] = 'MW/person'
    return boundaries[['PARISH','POP2001','consumption','ei','ei_uom','geometry',]]


def get_ei_by_parish():
    '''Get a dataframe of electricity intensities by parish
    '''
    elec_data = process_raw_consumption_data('../data/energy-demand/energy_consumption.csv')
    boundaries = gpd.read_file('../data/incoming_data/admin_boundaries.gpkg',layer='admin1')
    boundaries = append_energy_data_to_boundaries(boundaries,elec_data)
    return boundaries


def append_electricity_intensities(network,parish_col='parish'):
    '''Append electricity intensities to snkit network data in create_topology
    '''
    boundaries = get_ei_by_parish()
    ei_dict = boundaries.set_index('PARISH')['ei'].to_dict()
    # add parishes to nodes
    network.nodes = gpd.overlay(network.nodes,boundaries)
    # parish col
    network.nodes['parish'] = network.nodes['PARISH']
    # map electricity intensities by parish
    network.nodes['elec_intensity'] = network.nodes[parish_col].map(ei_dict)
    return network
