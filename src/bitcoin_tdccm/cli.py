"""Command-line entrypoints for the Bitcoin TDCCM analysis."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .config import DEFAULT_CONFIG, PAIRS, PROCESSED_PYEDM_DATA, RAW_DATA, REFERENCE_DIR
from .plotting import make_all_paper_figures, make_paper_figure
from .preprocessing import write_processed_data
from .tdccm import run_tdccm_pair, with_runtime_overrides


def preprocess_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Regenerate processed normalized-return CSVs.")
    parser.add_argument("--raw", type=Path, default=RAW_DATA)
    parser.add_argument(
        "--dated-output",
        type=Path,
        default=Path("data/processed/bitcoin_sp500_gold_normalized_log_returns_by_date.csv"),
    )
    parser.add_argument(
        "--pyedm-output",
        type=Path,
        default=Path("data/processed/bitcoin_sp500_gold_normalized_log_returns_pyedm.csv"),
    )
    args = parser.parse_args(argv)

    dated, pyedm = write_processed_data(args.raw, args.dated_output, args.pyedm_output)
    print(f"Wrote {args.dated_output} ({dated.shape[0]} rows)")
    print(f"Wrote {args.pyedm_output} ({pyedm.shape[0]} rows)")
    return 0


def run_tdccm_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run paper-parity TDCCM sweeps.")
    parser.add_argument("--data", type=Path, default=PROCESSED_PYEDM_DATA)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/tdccm"))
    parser.add_argument("--pair", choices=("all", *PAIRS.keys()), default="all")
    parser.add_argument("--num-processes", type=int, default=None)
    parser.add_argument("--sample", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args(argv)

    config = with_runtime_overrides(
        DEFAULT_CONFIG,
        num_processes=args.num_processes,
        sample=args.sample,
        seed=args.seed,
    )
    data = pd.read_csv(args.data)
    pair_names = tuple(PAIRS) if args.pair == "all" else (args.pair,)
    for pair_name in pair_names:
        pair = PAIRS[pair_name]
        pair_output = args.output_dir / pair.name
        print(f"Running {pair.name}; writing {pair_output}")
        run_tdccm_pair(data, pair, config=config, output_dir=pair_output)
    return 0


def make_figures_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Regenerate paper rho-per-window figures.")
    parser.add_argument("--input-root", type=Path, default=REFERENCE_DIR)
    parser.add_argument("--output-dir", type=Path, default=Path("figures"))
    parser.add_argument("--pair", choices=("all", *PAIRS.keys()), default="all")
    args = parser.parse_args(argv)

    if args.pair == "all":
        paths = make_all_paper_figures(args.input_root, args.output_dir)
    else:
        pair = PAIRS[args.pair]
        paths = [
            make_paper_figure(
                pair,
                input_dir=args.input_root / pair.name,
                output_path=args.output_dir / f"{pair.name.replace('-', '_')}_rho_per_window.pdf",
            )
        ]
    for path in paths:
        print(f"Wrote {path}")
    return 0
