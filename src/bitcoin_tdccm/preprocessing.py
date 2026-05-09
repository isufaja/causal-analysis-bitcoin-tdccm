"""Data preprocessing for the Bitcoin TDCCM analysis."""

from __future__ import annotations

from functools import reduce
from pathlib import Path

import numpy as np
import pandas as pd

from .config import ASSETS, PROCESSED_DATED_DATA, PROCESSED_PYEDM_DATA, RAW_DATA


def build_normalized_returns(
    raw_prices: pd.DataFrame,
    assets: tuple[str, ...] = ASSETS,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return dated and PyEDM-compatible normalized log-return data frames.

    This mirrors the original notebook method: each asset is cleaned, converted
    to log returns, z-score normalized independently, and then merged by date.
    The PyEDM-compatible output uses integer time labels matching the original
    PyEDM-compatible normalized-return artifact.
    """

    asset_frames: list[pd.DataFrame] = []
    for asset in assets:
        asset_df = raw_prices[["Date", asset]].copy()
        asset_df[asset] = pd.to_numeric(asset_df[asset], errors="coerce")
        asset_df = asset_df.dropna(subset=[asset])
        asset_df = asset_df[asset_df[asset] > 0].copy()

        log_return_col = f"{asset}_log_return"
        normalized_col = f"{asset}_normalized_log_return"
        asset_df[log_return_col] = np.log(asset_df[asset] / asset_df[asset].shift(1))
        asset_df = asset_df.dropna(subset=[log_return_col]).copy()

        mean = asset_df[log_return_col].mean()
        std = asset_df[log_return_col].std()
        if std == 0:
            std = np.finfo(float).eps
        asset_df[normalized_col] = (asset_df[log_return_col] - mean) / std
        asset_frames.append(asset_df[["Date", normalized_col]])

    dated = reduce(
        lambda left, right: pd.merge(left, right, on="Date", how="inner"),
        asset_frames,
    )
    dated = dated.sort_values("Date").reset_index(drop=True)

    pyedm = dated.rename(
        columns={f"{asset}_normalized_log_return": asset for asset in assets}
    ).copy()
    pyedm["Date"] = range(2, len(pyedm) + 2)
    pyedm = pyedm[["Date", *assets]]
    return dated, pyedm


def write_processed_data(
    raw_path: Path = RAW_DATA,
    dated_path: Path = PROCESSED_DATED_DATA,
    pyedm_path: Path = PROCESSED_PYEDM_DATA,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Regenerate and write both processed CSV artifacts."""

    raw_prices = pd.read_csv(raw_path)
    dated, pyedm = build_normalized_returns(raw_prices)
    dated_path.parent.mkdir(parents=True, exist_ok=True)
    pyedm_path.parent.mkdir(parents=True, exist_ok=True)
    dated.to_csv(dated_path, index=False)
    pyedm.to_csv(pyedm_path, index=False)
    return dated, pyedm
