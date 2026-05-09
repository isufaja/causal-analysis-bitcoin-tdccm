from __future__ import annotations

from pathlib import Path

from bitcoin_tdccm.config import PAIRS, REFERENCE_DIR
from bitcoin_tdccm.plotting import make_all_paper_figures, make_paper_figure


def test_make_single_paper_figure_from_reference_csvs(tmp_path: Path) -> None:
    output = make_paper_figure(
        PAIRS["btc-spx"],
        input_dir=REFERENCE_DIR / "btc-spx",
        output_path=tmp_path / "btc_spx_rho_per_window.pdf",
    )

    assert output.exists()
    assert output.stat().st_size > 0


def test_make_all_paper_figures_from_reference_csvs(tmp_path: Path) -> None:
    outputs = make_all_paper_figures(input_root=REFERENCE_DIR, output_dir=tmp_path)

    assert {path.name for path in outputs} == {
        "btc_spx_rho_per_window.pdf",
        "btc_gold_rho_per_window.pdf",
    }
    assert all(path.stat().st_size > 0 for path in outputs)
