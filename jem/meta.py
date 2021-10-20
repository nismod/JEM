'''
    metainfo.py
        Meta-data associated with the INFRASIM model

    @amanmajid
'''

metainfo = {
            'i_field'               : 'from_id',
            'j_field'               : 'to_id',
            'cost_column'           : 'length',
            'upper_bound'           : 'max',
            'lower_bound'           : 'min',
            'nodes_header'          : ['id','asset_type','subtype','title','capacity'],
            'edges_header'          : ['id','from_id','to_id','length','min','max'],
            'flow_header'           : [],
            'edge_index_variables'  : ['from_id','to_id','timestep'],
            'infrasim_cache'        : '../data/__infrasim__/',
            'outputs_figures'       : '../outputs/figures/',
            'outputs_data'          : '../outputs/statistics/',
            'temporal_resolution'   : 'daily'
            }
