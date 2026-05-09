# Applying Time Delay Convergent Cross Mapping to Bitcoin Time Series

![Overview of convergent cross mapping](figures/overview_ccm.png)

This repository contains the analysis code and data pipeline for applying Time Delay Convergent Cross Mapping (TDCCM) to Bitcoin, the S&P 500, and gold time series.

The project is based on:

> Isufaj, A., De Castro Martins, C., Cavazza, M., & Prendinger, H. (2025). Applying time delay convergent cross mapping to Bitcoin time series. *Expert Systems with Applications*, 277, 127125. https://doi.org/10.1016/j.eswa.2025.127125

## Overview

Financial time series often show nonlinear, time-varying behavior that is difficult to capture with standard linear causality methods. This project uses empirical dynamic modeling, sliding windows, and TDCCM to explore causal interactions between:

- Bitcoin and the S&P 500
- Bitcoin and gold

The code covers data preprocessing, normalized log-return generation, TDCCM sweeps across time lags, and final figure generation.

## Repository Structure

- `data/raw/`: daily BTC, S&P 500, and gold prices.
- `data/processed/`: normalized log returns used by PyEDM.
- `data/reference/`: saved TDCCM result tables used for fast figure regeneration.
- `figures/`: overview image and generated result figures.
- `src/bitcoin_tdccm/`: reusable preprocessing, TDCCM, and plotting modules.
- `scripts/`: command-line entrypoints for the main workflow.
- `tests/`: lightweight validation tests plus an optional full TDCCM parity test.

## Setup

Create the Conda environment:

```bash
conda env create -f environment.yml
conda activate tdccm
python -m pip install -e .
```

For an existing environment:

```bash
conda activate tdccm
python -m pip install -r requirements.txt
python -m pip install -e .
```

## Run

Regenerate normalized log returns:

```bash
python scripts/preprocess.py
```

Regenerate figures from saved TDCCM tables:

```bash
python scripts/make_figures.py --input-root data/reference --output-dir figures
```

Run the full TDCCM sweep:

```bash
python scripts/run_tdccm.py --pair all --output-dir outputs/tdccm
```

Run tests:

```bash
pytest
```

The full TDCCM parity test is intentionally opt-in because it is computationally expensive:

```bash
RUN_SLOW_TDCCM=1 pytest -m slow
```

## Method Notes

The default configuration is aligned with the saved paper result artifacts: 100-point sliding windows, 30-point steps, embedding search over `maxE=10`, PyEDM tau convention `-3..-1`, and TDCCM lags `Tp=-10..10`.

Two implementation details are worth noting:

- The paper text mentions a 20-point step, while the saved result tables contain 53 windows over 1,678 observations, matching a 30-point step.
- Final presentation figures use explicit window filters from the original analysis notebook. These filters are centralized in `bitcoin_tdccm.config.PAPER_FIGURE_FILTERS`.

PyEDM is pinned to the upstream v2.1.1 source commit used during the analysis for version consistency.
