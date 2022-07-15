# Jamaica Energy Model (JEM)
### A high-level power flow model of Jamaica's energy system

<img align="center" width="800" src="https://github.com/nismod/JEM/blob/main/demo/schematic.png">

This repository contains a simulation model for Jamaica's energy system formulated as an arc-node network. Based on a given supply and demand curve, JEM solves for flows of electricity across the network using linear programming.

**NOTE:** The tool is currently under development and all code published here is part of an on-going project.

### Contributors
**Project Lead:** Aman Majid (aman.majid@new.ox.ac.uk), University of Oxford <br>
**Principal Investigator:** [Professor Jim Hall](https://www.eci.ox.ac.uk/people/jhall.html), University of Oxford <br>
**Contributors and Collaborators**: <br>
[Raghav Pant](https://github.com/itrcrisks), University of Oxford <br>
[Tom Russell](https://github.com/tomalrussell), University of Oxford <br>
<!-- [JPS Co.](https://www.jpsco.com/), Jamaica <br> -->

<!-- ### What's Here
The repository contains the InfraSim source code. The model has been applied to a case-study from the Thames basin, England, and will be expanded to other cases in future. These cases serve as a guide for other users to apply the InfraSim model to their areas of interest. An overview of each directory within the repository is shown below.

_demo/_
- A Jupyter Notebook explaining the model theory, as well as a small demo model of a water-wastewater-energy network in London, UK.
- Updated December 2020

_data/demo/_
- **spatial**: Shapefiles of node and edge data that can be opened in QGis.
- **csv**: Time series demo nodal flow data.

_infrasim/_
- InfraSim source code related to the Thames system can be found in thames.py
- There are a series of other Python files that contain code for data pre-processing and post-processing.
- Model metadata, parameters, and assumptions can also be found here.

_qgis/_
- A QGis project file to explore the network spatial data.

_outputs/_
- All model outputs such as figures, data, and statistics are saved here. -->

### Requirements
The model requires [Gurobi](https://www.gurobi.com) and the associated [GurobiPy](https://www.gurobi.com) library for the optimisation. In addition, standard scientific libraries in Python are needed such as [pandas](https://pandas.pydata.org/), [numpy](https://numpy.org/), [matplotlib](https://matplotlib.org/) etc. Requirements for spatial network analysis include [QGis](https://www.qgis.org/en/site/), [geopandas](https://geopandas.org/install.html), and [snkit](https://github.com/tomalrussell/snkit).

<i>Note</i>: The Gurobi package requires a license for usage but this can be obtained freely for academic use. <!-- An open-source alternative version of the model is currently being developed in the [PuLP](https://github.com/coin-or/pulp) library and the [Julia](https://julialang.org) programming language.   -->

### Getting started
Clone or download this repository.

Get a [Gurobi license](https://www.gurobi.com/downloads/)

Create project enviroment using the config file in this directory (only tested on macOS Big Sur):

```
mamba env update -n JEM --file environment.yml
conda activate ./env
```

or

```
conda env create --prefix ./env --file environment.yml
conda activate ./env
```

See the [demo notebook](https://github.com/amanmajid/InfraSim/blob/main/demo/demo.ipynb) for a small demonstration.

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
