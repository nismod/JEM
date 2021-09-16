# -*- coding: utf-8 -*-
"""
Created on Thu Sep 16 10:02:20 2021

@author: aqua
"""

import geopandas as gpd
import pandas as pd
#import qgis.core as gis


#---------------
# Append consumption data to parish shapefile

# read raw data
path    = '../data/spatial/admin-boundaries.shp'
admin   = gpd.read_file(path)

# dissolve
parish = admin.dissolve(by='Parish', aggfunc='sum').reset_index()

# read energy consumption data
path    = '../data/energy-demand/energy_consumption.csv'
energy  = pd.read_csv(path)
energy  = energy[['PARISH','Year','PARISH TOTAL']]

# pivot data
energy  = energy.pivot(index='PARISH',columns='Year')
energy.columns = [str(i[1]) for i in energy.columns.values]
energy = energy.reset_index()

# convert str to data
for col in ['2014', '2015', '2016', '2017', '2018', '2019', '2020',]:
    energy[col] = energy[col].str.strip().str.replace(',','')
    energy[col] = energy[col].astype(float)
    
# rename
energy['Parish'] = energy['PARISH']
energy.Parish = energy.Parish.str.replace('St.', 'St')
energy.Parish = energy.Parish.str.replace('KSAN', 'KSA')
energy.Parish = energy.Parish.str.replace('KSAS', 'KSA')

energy = energy.groupby(by=['Parish']).sum().reset_index()

# merge
parish = parish.merge(energy,on=['Parish'])

# save
parish.to_file(driver='ESRI Shapefile', filename='../data/energy-demand/energy_demand.shp')

sinks_path  = 'D:/OneDrive - Nexus365/Work/JEM/_tmp/sinks.shp|layername=sinks'
output_path = 'D:/OneDrive - Nexus365/Work/JEM/data/energy-demand/voronoi-sinks.gpkg'

# # run voronoi polygons process
# processing.run("qgis:voronoipolygons",
#                {'INPUT':sinks_path,
#                 'BUFFER':0,
#                 'OUTPUT':output_path})