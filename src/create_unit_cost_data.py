'''

    create_unit_cost_date.py
    
        This script produces unit costs ($/MW and $/km) for energy sector
            assets based on the World Bank's Private Participation in 
            Infrastructure (PPI) dataset. The unit costs are derived for energy
            supply assets (e.g. solar, wind, gas) and transmission lines.
    
@amanmajid
'''


# modules
import pandas as pd
import numpy as np

#----
# FUNCTIONS

def adjust_for_inflation(values,years,rpi=3.0):
    ''' adjust for inflation
    '''
    return values * (1+rpi/100) ** years
    

#----
# PRE-PROCESS

# fetch data
path_to_data = '../data/_raw/world_bank_ppi/energy_sector_costs.csv'
ppi_data = pd.read_csv(path_to_data)

# get cols of interest
cols = ['Region','Country','IncomeGroup','Project name','Technology',
        'Capacity','CapacityType','TotalInvestment','InvestmentYear']

# reindex cols
ppi_data = ppi_data[cols]

# replace str types in rows
for i in ['N/A, N/A','N/A','Not Applicable, N/A','Not Applicable','Not Available']:
    ppi_data.Capacity = ppi_data.Capacity.replace(i,np.nan)
    ppi_data.TotalInvestment = ppi_data.TotalInvestment.replace(i,np.nan)


# get jamaican features
features = {'Region' : ppi_data.loc[ppi_data.Country.isin(['Jamaica']),'Region'].iloc[0],
            'IncomeGroup' : ppi_data.loc[ppi_data.Country.isin(['Jamaica']),'IncomeGroup'].iloc[0],
            'assets' : ['wind','solar','gas','hydro','substation','diesel']}


# get data for regions within same income group as jamaica
ppi_data = ppi_data.loc[ppi_data.IncomeGroup.isin([features['IncomeGroup']])].reset_index(drop=True)

# get data for relevant capacity types
ppi_data = ppi_data.loc[ppi_data.CapacityType.isin(['MW','KM'])].reset_index(drop=True)

# convert types
ppi_data.TotalInvestment = ppi_data.TotalInvestment.astype('float')
ppi_data.Capacity = ppi_data.Capacity.astype('float')

# add transmission to technologies
ppi_data.loc[ppi_data['Project name'].str.contains('transmission',case=False),'Technology'] = 'Transmission'

# remove gas pipelines
ppi_data = ppi_data.loc[~ppi_data['Project name'].str.contains('natural gas transmission',case=False)].reset_index(drop=True)
ppi_data = ppi_data.loc[~ppi_data['Project name'].str.contains('pipeline',case=False)].reset_index(drop=True)
   

#----
# COMPUTE

# compute inflation year
ppi_data['inflation_years'] = 2020 - ppi_data['InvestmentYear']

# adjust investment by inflation
ppi_data['investment_infl_adjusted'] = adjust_for_inflation(ppi_data.TotalInvestment,ppi_data.inflation_years)

# unit costs
ppi_data['unit_cost']       = ppi_data['investment_infl_adjusted'].divide(ppi_data['Capacity'])
ppi_data['unit_cost_uom']    = ''

# unit cost uom
ppi_data.loc[ppi_data.CapacityType.str.contains('MW',case=False),'unit_cost_uom'] = 'USD/MW'
ppi_data.loc[ppi_data.CapacityType.str.contains('KM',case=False),'unit_cost_uom'] = 'USD/km'

# groupby
minimum = ppi_data.groupby(by='Technology').min().reset_index()[['Technology','unit_cost']]
maximum = ppi_data.groupby(by='Technology').max().reset_index()[['Technology','unit_cost']]
mean = ppi_data.groupby(by='Technology').mean().reset_index()[['Technology','unit_cost']]

# combine
unit_costs = mean.copy()
#unit_costs['unit_cost_min'] = minimum.unit_cost.multiply(10**6)
unit_costs['unit_cost_avg'] = mean.unit_cost.multiply(10**6)
unit_costs['unit_cost_max'] = maximum.unit_cost.multiply(10**6)

# reindex
unit_costs = unit_costs[['Technology','unit_cost_avg','unit_cost_max']]
techs = ['Natural Gas','Solar, PV','Diesel','Hydro, Large (>50MW)','Hydro, Small (<50MW)','Wind','Transmission']
unit_costs = unit_costs.loc[unit_costs.Technology.isin(techs)]

# save
unit_costs.to_csv('../data/costs_and_damages/unit_costs.csv',index=False)