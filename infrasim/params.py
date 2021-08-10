'''
    constants.py
        Assumed constants in the INFRASIM model

    @amanmajid
'''

variables = {
            'demand_growth_rate'                : 0.028,
            # -HOUSEHOLD
            'household_water_demand_showering'  : 0,            # % total demand
            'household_water_demand_laundry'    : 0,            # % total demand
            'household_water_demand_toilets'    : 0,            # % total demand
            'household_water_demand_taps'       : 0,            # % total demand
            'household_water_demand_external'   : 0,            # % total demand
            'household_water_demand_dish_wash'  : 0,            # % total demand
            }


constants = {
            # -WATER SUPPLY
            'water_network_coverage'            : 1,            # m
            'surface_water_pumping_ei'          : 500,          # kWh/ML.m
            'groundwater_pumping_ei'            : 5,            # kWh/ML.m
            'groundwater_pumping_height'        : 10,           # m
            'desalination_brackish_ei'          : 2000,         # kWh/ML
            'desalination_ocean_ei'             : 3890,         # kWh/ML
            'water_treatment_ei'                : 300,          # kWh/ML
            # -WASTEWATER
            'water_to_wastewater_capture'       : 0.95,         # %
            'wastewater_treatment_ei'           : 200,
            'wastewater_network_coverage'       : 1,            # m
            'wastewater_network_capacity'       : 200,          # ML
            'wastewater_pumping_ei'             : 200,          # kWh/ML.m
            'wastewater_BOD_standard'           : 22,           # mg/L
            'wastewater_COD_standard'           : 50,           # mg/L
            'wastewater_SSs_standard'           : 25,           # mg/L
            'wastewater_NH3_standard'           : 8,            # mg/L
            'wastewater_plant_minimum_flow'     : 0,            # % of plant capacity
            # -ELECTRICITY
            'baseload_coefficient'              : 0.5,
            'storage_loss_coefficient'          : 0.1,
            'peak_demand_reserve'               : 0.2,
            'ocgt_ramping_rate'                 : 1200,         # MW/h
            'ccgt_ramping_rate'                 : 600,          # MW/h
            'coal_ramping_rate'                 : 260,          # MW/h
            'solar_ramping_rate'                : 12000,        # MW/h
            'wind_ramping_rate'                 : 3000,         # MW/h
            'nuclear_ramping_rate'              : 1200,         # MW/h
            'pumped_hydro_ramping_rate'         : 12000,        # MW/h
            'diesel_ramping_rate'               : 420,          # MW/h
            # -HOUSEHOLD
            'showering_ei'                      : 420,          # kWh/ML
            # -OTHER
            'super_source_maximum'              : 10**12,
            'mask_value'                        : -999,
            }
