electricity_network_vx.x.gpkg

@amanmajid
07/09/2021


---
GENERAL INFORMATION
---


Overview:
--------
	This dataset was created based on the NSBDM data collected by Edson Williams, as well as some 
	data scraped from JPS reports and OpenStreetMap. It maps the electricity system as: supply sites,
	substations, high voltage transmission, substations/poles, low voltage transmission, and demand. 


Versions:
--------

	VERSION 3.0
		- Added additional hydropower nodes
		- Population updated using latest outputs from TR
		- The above correction fixes demand assignment in the northern part of the island
		- Known issues:
			1. Topology around substations is incorrect in parts
			2. Some multilinestring data is not being properly processed by snkit functions
			   and is hence dropped from the dataset

	VERSION 2.0
		- Voronoi of population assignment added
		- Known issues:
			1. Topology around substations is incorrect in parts
			2. Some multilinestring data is not being properly processed by snkit functions
			   and is hence dropped from the dataset
			3. Hydro power plant locations unknown [fix in progress]
			4. Demand assignment around north of island is incorrect due to errors in admin boundary layer

	VERSION 1.2
		- Costs are now provided as totals ($US) in addition to unit costs ($/MW or $/MW/km)
		- Demand nodes are now treated the same as utility poles
		- Naming convention changed to: nodes and edges
		- Known issues:
			1. Topology around substations is incorrect in parts
			2. Some multilinestring data is not being properly processed by snkit functions
			   and is hence dropped from the dataset
			3. Hydro power plant locations unknown

	VERSION 1.1
		- Added capacity attributes to nodes (col: capacity) and edges (col: max)
		- Known issues:
			1. Topology around substations is incorrect in parts
			2. Some multilinestring data is not being properly processed by snkit functions
			   and is hence dropped from the dataset

	VERSION 1.0
		- Added population and energy intensity data
		- Energy demands can now be computed based on population and energy intensity
		- Known issues:
			1. Topology around substations is incorrect in parts
			2. Some multilinestring data is not being properly processed by snkit functions
			   and is hence dropped from the dataset

	VERSION 0.2
		- Added unit cost data
		- Known issues:
			1. Topology around substations is incorrect in parts
			2. Some multilinestring data is not being properly processed by snkit functions
			   and is hence dropped from the dataset
			3. Supply and demand has not yet been mapped 


	VERSION 0.1
		- Network topology refined using JEM/src/create_topology.py and manual cleaning
		- Network components were combined to create a single topology
		- Known issues:
			1. Unit costs missing from node and edge data
			2. Topology around substations is incorrect in parts
			3. Some multilinestring data is not being properly processed by snkit functions
			   and is hence dropped from the dataset
			4. Supply and demand has not yet been mapped 


	VERSION 0.0
		- First tidy version based on NSBDM data
		- Included synthetic power station and pole data (based on edge partitions)
		- Power station data was collected from OSM/Webscraping 
		- Known issues:
			1. Network split into hundreds of smaller components due to missing/inconsistent data
			2. Edge data contains empty datasets, duplicates and incorrect data
			3. Network topology incorrect in many places 


Future releases:
--------

The following features will be incorporated in the next release (minor revisions):
	- Topology around substations to be fixed
	- Unit costs to be incorporated into node and edge data