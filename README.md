![Python > 3.9](https://img.shields.io/badge/python-%3E%3D3.9-blue)
![Maintenance](https://img.shields.io/badge/status-maintenance-blue)

# Jamaica Energy Model (JEM) - a high-level power flow model of Jamaica's energy system

This repository contains a simulation model for Jamaica's energy system formulated as an arc-node network. Based on a given supply and demand curve, JEM solves for flows of electricity across the network using linear programming. 

This tool was initially developed in 2021-2 for a [CCRI](https://resilientinvestment.org/) project by researchers at [OPSIS, University of Oxford](https://opsis.eci.ox.ac.uk/).

### Contributors
**Project Lead:** Aman Majid (aman.majid@new.ox.ac.uk), University of Oxford <br>
**Principal Investigator:** [Professor Jim Hall](https://www.eci.ox.ac.uk/people/jhall.html), University of Oxford <br>
**Contributors and Collaborators**: <br>
- [Tom Russell](https://github.com/tomalrussell), University of Oxford <br>
- [Nadia Leonova](https://github.com/nnleonova), University of Oxford <br>
- [Raghav Pant](https://github.com/itrcrisks), University of Oxford <br>

### Requirements
The model requires [Gurobi](https://www.gurobi.com) and the associated [GurobiPy](https://www.gurobi.com) library for the optimisation. In addition, standard scientific libraries in Python are needed such as [pandas](https://pandas.pydata.org/), [numpy](https://numpy.org/), [matplotlib](https://matplotlib.org/) etc. Requirements for spatial network analysis include [QGIS](https://www.qgis.org/en/site/), [geopandas](https://geopandas.org/install.html), and [snkit](https://github.com/tomalrussell/snkit).

<i>Note</i>: The Gurobi package requires a license for usage but this can be obtained freely for academic use.

### Getting started
- Clone or download this repository.
- Get a [Gurobi license](https://www.gurobi.com/downloads/)
- Create project enviroment using `micromamba` and the config file in this directory:

```bash
micromamba env create -f environment.yml -y
micromamba activate jem-env
```

- or using your preferred Python package manager and virtual environment, navigate to the JEM repository and install it as a package by running:

```bash
pip install -e .
```

- See the [demo notebook](./notebook/demo.ipynb) for a small demonstration.

### Support
This work was initially supported by the [Coalition for Climate Resilient Investment (CCRI)](https://resilientinvestment.org/) project on creating a platform for infrastructure risk assessment and resilient investment prioritisation in Jamaica and is funded by the [UK Foreign, Commonwealth and Development Office (FCDO)](https://www.gov.uk/government/organisations/foreign-commonwealth-development-office).

### License
Copyright (C) 2020-2024 Aman Majid and the authors. All versions released under the [MIT License](https://opensource.org/licenses/MIT).
