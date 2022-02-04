# run_node_impact_assessment.py

This script is used to run a single-point failure analysis on the electricity nodal dataset. The process involves 'attacking' nodes one at a time and simulating the operations in the energy network, and then evaluating the sink nodes impacted. The files are setup to be run on the [ARC](https://www.arc.ox.ac.uk) linux server.

### Getting started
Download and clone this repository.

Get a [Gurobi license](https://www.gurobi.com/downloads/)

Create project enviroment using the config file in this directory (only tested on macOS Big Sur):

   conda env create --prefix ./env --file config.yml
   conda activate ./env

See the [demo notebook](https://github.com/amanmajid/InfraSim/blob/main/demo/demo.ipynb) for a small demonstration. -->

<!-- ### To Do
- Implement the InfraSim model using Julia code to allow users to choose their solver

### Future extensions
- InfraSim.JV: a model for the energy-water system in Israel, Palestine, and Jordan
- InfraSim.Jamaica: a model for the water system in Jamaica -->

<!-- ### Citing Research
Coming soon... -->

### Support
This work is supported part of the [Coalition for Climate Resilient Investment (CCRI)](https://resilientinvestment.org/) project on creating a platform for infrastructure risk assessment and resilient investment prioritisation in Jamaica and is funded by the [UK Foreign, Commonwealth and Development Office (FCDO)](https://www.gov.uk/government/organisations/foreign-commonwealth-development-office).

### License
Copyright (C) 2020 Aman Majid. All versions released under the [MIT License](https://opensource.org/licenses/MIT).
