from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from bitcoin_tdccm.config import DEFAULT_CONFIG, PAIRS, PROCESSED_PYEDM_DATA, REFERENCE_DIR
from bitcoin_tdccm.tdccm import reference_filename, run_tdccm_pair


pytestmark = pytest.mark.slow


def test_full_tdccm_reference_parity(tmp_path: Path) -> None:
    if os.environ.get("RUN_SLOW_TDCCM") != "1":
        pytest.skip("Set RUN_SLOW_TDCCM=1 to run the full TDCCM parity test.")
    pytest.importorskip("pyEDM")

    data = pd.read_csv(PROCESSED_PYEDM_DATA)
    for pair in PAIRS.values():
        output_dir = tmp_path / pair.name
        run_tdccm_pair(data, pair, DEFAULT_CONFIG, output_dir=output_dir)

        for source, target in (
            (pair.variable1, pair.variable2),
            (pair.variable2, pair.variable1),
        ):
            filename = reference_filename(source, target)
            actual = pd.read_csv(output_dir / filename)
            expected = pd.read_csv(REFERENCE_DIR / pair.name / filename)
            assert_frame_equal(actual, expected, check_dtype=False, atol=1e-9, rtol=1e-9)
