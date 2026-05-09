"""Paper figure generation from TDCCM result CSVs."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from .config import FIGURES_DIR, PAPER_FIGURE_FILTERS, PAIRS, REFERENCE_DIR, PairConfig
from .tdccm import direction_key, reference_filename


TP_COLORS = (
    "red",
    "blue",
    "green",
    "orange",
    "purple",
    "brown",
    "pink",
    "gray",
    "olive",
    "cyan",
    "magenta",
    "yellow",
    "gold",
    "navy",
    "teal",
    "maroon",
    "lime",
    "turquoise",
    "beige",
    "lavender",
)


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

    unique_tp = np.unique(np.concatenate((forward["Tp"].to_numpy(), reverse["Tp"].to_numpy())))
    colors = list(TP_COLORS)
    if len(unique_tp) > len(colors):
        repeats = int(np.ceil(len(unique_tp) / len(colors)))
        colors *= repeats
    tp_to_color = {tp: colors[idx] for idx, tp in enumerate(sorted(unique_tp))}

    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)
    ax.plot(forward["Window"], forward["rho"], color="black", linestyle="-", label=forward_key)
    ax.scatter(
        forward["Window"],
        forward["rho"],
        c=[tp_to_color[tp] for tp in forward["Tp"]],
        edgecolor="k",
        s=100,
        zorder=3,
        marker="o",
    )
    ax.plot(reverse["Window"], reverse["rho"], color="lightgray", linestyle="-", label=reverse_key)
    ax.scatter(
        reverse["Window"],
        reverse["rho"],
        c=[tp_to_color[tp] for tp in reverse["Tp"]],
        edgecolor="k",
        s=100,
        zorder=3,
        marker="s",
    )

    ax.axvline(x=23, color="black", linestyle="--")
    ax.axvline(x=38, color="black", linestyle="--")
    ax.set_xlabel("Window")
    ax.set_ylabel("Highest Rho Value")
    ax.set_title(f"Highest Rho Value per Window for {pair.variable1} and {pair.variable2}")
    ax.grid(True)

    legend_elements = [
        *(Patch(facecolor=tp_to_color[tp], edgecolor="k", label=f"Tp={tp}") for tp in sorted(unique_tp)),
        Line2D([0], [0], color="black", linestyle="-", label=forward_key),
        Line2D([0], [0], color="lightgray", linestyle="-", label=reverse_key),
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor="black",
            markersize=10,
            label=f"{forward_key} marker",
            markeredgecolor="k",
        ),
        Line2D(
            [0],
            [0],
            marker="s",
            color="w",
            markerfacecolor="black",
            markersize=10,
            label=f"{reverse_key} marker",
            markeredgecolor="k",
        ),
        Line2D([0], [0], color="black", linestyle="--", label="COVID-19 period"),
    ]
    ax.legend(handles=legend_elements, loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0.0)
    fig.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, format="pdf", bbox_inches="tight")
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
