from __future__ import annotations

import pandas as pd
from pandas.testing import assert_frame_equal

from bitcoin_tdccm.config import PROCESSED_DATED_DATA, PROCESSED_PYEDM_DATA, RAW_DATA
from bitcoin_tdccm.preprocessing import build_normalized_returns


def test_preprocessing_recreates_checked_processed_data() -> None:
    raw = pd.read_csv(RAW_DATA)
    dated, pyedm = build_normalized_returns(raw)

    expected_dated = pd.read_csv(PROCESSED_DATED_DATA)
    expected_pyedm = pd.read_csv(PROCESSED_PYEDM_DATA)

    assert_frame_equal(dated, expected_dated, check_dtype=False, atol=1e-12, rtol=1e-12)
    assert_frame_equal(pyedm, expected_pyedm, check_dtype=False, atol=1e-12, rtol=1e-12)
