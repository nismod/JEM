'''

map_water_assets.py

    This script creates mapping between the JEM nodal file and the nismod.jamaica.water 
    sector assets. Specifically, it links each energy-consumptive water asset to the nearest
    utility pole or substation in the energy sector nodal file. 
    

'''

import geopandas as gpd
from shapely.ops import nearest_points
from tqdm import tqdm

print('loading data...')
elec_nodes = gpd.read_file('../data/spatial/infrasim-network/nodes.shp')
water_nodes = gpd.read_file('../data/water/merged_water_assets.shp')
print('done')

water_id_col = 'node_id'
output_col_name_water = 'water_node_id'
output_col_name_elect = 'elec_node_id'

# index nodes
print('indexing node data...')
# gpd1 = elec_nodes.loc[elec_nodes.subtype.isin(['pole','substation'])].reset_index(drop=True).copy()
gpd1 = elec_nodes.loc[elec_nodes.asset_type.isin(['sink'])].reset_index(drop=True).copy()
gpd2 = water_nodes.loc[water_nodes.linkage == 'True'].reset_index(drop=True).copy()

# form unary union
pts3 = gpd1.geometry.unary_union
# init elec_asset column
gpd2[output_col_name_elect] = ''

# loop through each water asset
print('looping across water nodes to map energy assets...')
for i, row in gpd2.iterrows():
    nearest_elec_asset = nearest_points(row.geometry, pts3)[1]
    gpd2.loc[i,output_col_name_elect] = gpd1.loc[gpd1.geometry.within(nearest_elec_asset),'id'].values[0]
# append water nodes
water_nodes[output_col_name_elect] = water_nodes[water_id_col].map(\
                gpd2.set_index(water_id_col)[output_col_name_elect].to_dict())
print('done')

#rename columsn
water_nodes[output_col_name_water] = water_nodes[water_id_col]

# save to shapefile
print('saving file...')
water_nodes.to_file(driver='ESRI Shapefile',filename='../data/water/mapped_water_assets.shp')
# save to csv
water_nodes[[output_col_name_water,output_col_name_elect]].to_csv('../data/water/mapped_water_assets.csv',index=False)
print('done')
print('files saved to: ../data/water/mapped_water_assets.shp')