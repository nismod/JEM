# -*- coding: utf-8 -*-
"""

    create_flow_data.py
    
        Script to produce supply and demand data. 
        
        Workflow:
            - Merge Multilinestrings from power line data       [Complete]
            - Add junction nodes where lines split              [Complete]
            - Add sink nodes to low voltage                     [TO DO]
            - Connect supply to substations                     [TO DO]
            - Create bi-directional high voltage grid           [TO DO]
            - Connect high voltage grid to low voltage grid     [TO DO]
            - Save processed spatial data                       [Complete]

"""