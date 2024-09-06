#!/usr/bin/env python
# coding: utf-8
"""Associate power system failure with economic losses
"""
import sys
from glob import glob
from pathlib import Path

import pandas as pd
from tqdm.auto import tqdm


def main(base_path):
    node_gdp = pd.read_csv(
        base_path
        / "processed_data/networks_economic_activity/electricity_dependent_economic_activity.csv",
        index_col="id",
        usecols=["id", "total_GDP"],
    )
    output_dir = base_path / "results/grid_failures/cell_disruption_loss"
    output_dir.mkdir(exist_ok=True)

    grid_disruptions = read_csvs(base_path / "results/grid_failures/cell_disruption/")
    for disruption in grid_disruptions:
        disruption.set_index("affected_node_id", inplace=True)
        grid_id = disruption.grid_id.iloc[0]
        disruption_loss = disruption.join(node_gdp).rename(
            columns={"total_GDP": "loss_gdp"}
        )
        disruption_loss["loss_gdp_unit"] = "JD/day"
        disruption_loss.to_csv(output_dir / f"loss_{grid_id}.csv")


def read_csvs(csv_dir):
    for csv in tqdm(glob(str(csv_dir / "*.csv"))):
        yield pd.read_csv(csv)


if __name__ == "__main__":
    base_path = Path(sys.argv[1])
    main(base_path)
