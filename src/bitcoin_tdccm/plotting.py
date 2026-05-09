"""Paper figure generation from TDCCM result CSVs."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from .config import FIGURES_DIR, PAPER_FIGURE_FILTERS, PAIRS, REFERENCE_DIR, PairConfig
from .tdccm import direction_key, reference_filename


PAPER_BLUE = "#1f77b4"
PAPER_ORANGE = "#ff7f0e"


def max_rho_by_window(
    heatmap_df: pd.DataFrame,
    windows_to_remove: tuple[int, ...] = (),
) -> pd.DataFrame:
    """Select each window's maximum rho row, then apply paper-figure filters."""

    selected = heatmap_df.loc[
        heatmap_df.groupby("Window")["rho"].idxmax()
    ][["Window", "Tp", "rho"]].reset_index(drop=True)
    selected = selected[selected["Tp"] <= 0]
    if windows_to_remove:
        selected = selected[~selected["Window"].isin(windows_to_remove)]
    return selected.sort_values("Window").reset_index(drop=True)


def _read_direction(input_dir: Path, source: str, target: str) -> pd.DataFrame:
    path = input_dir / reference_filename(source, target)
    if not path.exists():
        raise FileNotFoundError(f"Missing TDCCM result CSV: {path}")
    return pd.read_csv(path)


def make_paper_figure(
    pair: PairConfig,
    input_dir: Path | None = None,
    output_path: Path | None = None,
) -> Path:
    """Create the final rho-per-window figure for one paper pair."""

    input_dir = input_dir or pair.reference_dir
    output_path = output_path or FIGURES_DIR / f"{pair.name.replace('-', '_')}_rho_per_window.pdf"

    forward_key = direction_key(pair.variable1, pair.variable2)
    reverse_key = direction_key(pair.variable2, pair.variable1)
    filters = PAPER_FIGURE_FILTERS[pair.name]

    forward = max_rho_by_window(
        _read_direction(input_dir, pair.variable1, pair.variable2),
        filters[forward_key],
    )
    reverse = max_rho_by_window(
        _read_direction(input_dir, pair.variable2, pair.variable1),
        filters[reverse_key],
    )

    forward_label = f"{pair.variable1} to {pair.variable2}"
    reverse_label = f"{pair.variable2} to {pair.variable1}"

    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    ax.plot(
        forward["Window"],
        forward["rho"],
        color=PAPER_BLUE,
        linestyle="-",
        marker="o",
        markersize=4,
        linewidth=1,
        label=forward_label,
    )
    ax.plot(
        reverse["Window"],
        reverse["rho"],
        color=PAPER_ORANGE,
        linestyle="-",
        marker="o",
        markersize=4,
        linewidth=1,
        label=reverse_label,
    )

    ax.axvline(x=23, color=PAPER_BLUE, linestyle="--", linewidth=1, label="Start of COVID-19")
    ax.axvline(x=38, color=PAPER_ORANGE, linestyle="--", linewidth=1, label="End of COVID-19")
    y_top = max(forward["rho"].max(), reverse["rho"].max())
    y_text = y_top + 0.01
    ax.text(23, y_text, "Start of COVID-19", color=PAPER_BLUE, fontsize=8)
    ax.text(38, y_text, "End of COVID-19", color=PAPER_ORANGE, fontsize=8)
    ax.set_xlabel("Window")
    ax.set_ylabel("Highest Rho Value")
    ax.set_title(
        f"Highest Rho Value per Window for {pair.variable1} and {pair.variable2} (log returns)"
    )
    ax.grid(True)
    ax.legend(loc="upper left")
    fig.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, format="pdf")
    plt.close(fig)
    return output_path


def make_all_paper_figures(
    input_root: Path = REFERENCE_DIR,
    output_dir: Path = FIGURES_DIR,
    pairs: tuple[str, ...] = tuple(PAIRS),
) -> list[Path]:
    """Create final paper figures for all requested pairs."""

    output_paths: list[Path] = []
    for pair_name in pairs:
        pair = PAIRS[pair_name]
        output_paths.append(
            make_paper_figure(
                pair,
                input_dir=input_root / pair.name,
                output_path=output_dir / f"{pair.name.replace('-', '_')}_rho_per_window.pdf",
            )
        )
    return output_paths
