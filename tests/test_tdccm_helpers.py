from __future__ import annotations

import pandas as pd
import pytest
from dataclasses import replace

from bitcoin_tdccm.config import DEFAULT_CONFIG, PAIRS, PROCESSED_PYEDM_DATA
from bitcoin_tdccm.tdccm import (
    compute_max_lib_size,
    direction_key,
    reference_filename,
    run_tdccm_window,
    window_slices,
)


def test_window_slices_match_reference_window_count() -> None:
    data = pd.DataFrame({"x": range(1678)})
    slices = window_slices(len(data), DEFAULT_CONFIG)

    assert len(slices) == 53
    assert slices[0] == (0, 0, 100)
    assert slices[-1] == (52, 1560, 1660)


def test_compute_max_lib_size_uses_embedding_tau_and_tp() -> None:
    assert compute_max_lib_size(n_rows=100, embedding_dim=4, tau=-3, tp=-10) == 81
    assert compute_max_lib_size(n_rows=100, embedding_dim=1, tau=-3, tp=9) == 91


def test_direction_file_naming_is_stable() -> None:
    assert direction_key("BTC", "SPX") == "BTC_to_SPX"
    assert reference_filename("BTC", "SPX") == "norm_heatmap_data_BTC_to_SPX.csv"


def test_run_tdccm_window_smoke() -> None:
    pytest.importorskip("pyEDM")
    data = pd.read_csv(PROCESSED_PYEDM_DATA).head(40).reset_index(drop=True)
    config = replace(
        DEFAULT_CONFIG,
        window_size=40,
        max_embedding_dim=2,
        tau_values=(-1,),
        tp_values=(-1, 0, 1),
        num_processes=1,
        sample=2,
        lib_sizes_min=5,
        lib_sizes_step=5,
    )

    results = run_tdccm_window(data, 0, PAIRS["btc-spx"], config)

    assert set(results) == {"BTC_to_SPX", "SPX_to_BTC"}
    assert len(results["BTC_to_SPX"]) == 3
    assert all(set(row) == {"Window", "Tp", "rho"} for row in results["BTC_to_SPX"])
