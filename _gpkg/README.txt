electricity_network_v0.1.gpkg

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