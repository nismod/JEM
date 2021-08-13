# -*- coding: utf-8 -*-
"""
Created on Thu Jul 29 11:04:55 2021

@author: aqua
"""

import pandas as pd
import seaborn
import numpy as np



#-----------------
# Function

def return_interp1(x,y,data):
    # create x-array
    xx = np.linspace(0,120,13)
    # interpolate for each x-value
    yy = [np.interp(i,data[x],data[y]) for i in xx]
    # return
    return xx,yy

def return_interp2(x,y,data):
    # create x-array
    xx = np.linspace(0,5,11)
    # interpolate for each x-value
    yy = [np.interp(i,data[x],data[y]) for i in xx]
    # return
    return xx,yy

#=============================================================================
# WIND SPEEDS
#=============================================================================


# Load data

# set base path
basepath = '../data/_raw/costs_and_damages/'

# files
path1 = ['extract_wind_speed_substation.csv',
         'extract_wind_speed_transmission.csv',
         'extract_wind_speed_power_plant.csv',
         'extract_wind_speed_poles.csv']

# load data
substation      = pd.read_csv(basepath+path1[0])
transmission    = pd.read_csv(basepath+path1[1])
power_plant     = pd.read_csv(basepath+path1[2])
poles           = pd.read_csv(basepath+path1[3])


# Interpolate

# init blank data frame
outputs = pd.DataFrame()

# substation
x,y = return_interp1(x='wind speed', y='% failure', data=substation)
outputs['wind_speed_m/s'],outputs['substation'] = x,y

# transmission
_,y = return_interp1(x='wind speed', y='% failure', data=transmission)
outputs['transmission'] = y

# poles
_,y = return_interp1(x='wind speed', y='% failure', data=poles)
outputs['poles'] = y

# poles
_,y1 = return_interp1(x='wind m/s', y='DS4', data=power_plant)
_,y2 = return_interp1(x='wind m/s', y='DS3', data=power_plant)
_,y3 = return_interp1(x='wind m/s', y='DS2', data=power_plant)
_,y4 = return_interp1(x='wind m/s', y='DS1', data=power_plant)

outputs['power_plant_ds4'] = y1
outputs['power_plant_ds3'] = y2
outputs['power_plant_ds2'] = y3
outputs['power_plant_ds1'] = y4

# add assets we ignore
outputs['wind_farm']    = 0
outputs['hydro_plant']  = 0
outputs['solar_farm']   = ''

# save
outputs.to_csv('../data/costs_and_damages/wind_speed_electricity.csv',index=False)



#=============================================================================
# FLOODING
#=============================================================================


# Load data
substation      = pd.read_csv(basepath+'extract_flooding_substation.csv')
power_plant     = pd.read_csv(basepath+'extract_flooding_power_plants.csv')


# Interpolate

# init blank data frame
outputs = pd.DataFrame()

# substation
x,y = return_interp2(x='flood_depth', y='% failure', data=substation)
outputs['flood_depth_m'],outputs['substation'] = x,y

# transmission
_,y = return_interp2(x='flood_depth', y='% failure', data=power_plant)
outputs['power_plant'] = y

# add assets we ignore
outputs['wind_farm']        = 0
outputs['hydro_plant']      = ''
outputs['solar_farm']       = 0
outputs['transmission']     = 0

# save
outputs.to_csv('../data/costs_and_damages/flooding_electricity.csv',index=False)