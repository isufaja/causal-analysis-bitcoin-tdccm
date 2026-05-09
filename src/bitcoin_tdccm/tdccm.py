"""Paper-parity TDCCM execution helpers."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .config import DEFAULT_CONFIG, PairConfig, TDCCMConfig


def require_pyedm() -> Any:
    """Import pyEDM with a clear error if the dependency is missing."""

    try:
        import pyEDM as EDM
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "pyEDM is required for TDCCM runs. Install with `python -m pip install -e .` "
            "or `python -m pip install pyEDM==2.1.1`."
        ) from exc
    return EDM


def compute_max_lib_size(n_rows: int, embedding_dim: int, tau: int, tp: int) -> int:
    """Maximum allowable CCM library size for a window and lag."""

    return n_rows - (embedding_dim - 1) * abs(tau) - abs(tp)


def window_slices(
    n_rows: int,
    config: TDCCMConfig = DEFAULT_CONFIG,
) -> list[tuple[int, int, int]]:
    """Return `(window_id, start, end)` slices used in the paper-parity run."""

    return [
        (window_id, start, start + config.window_size)
        for window_id, start in enumerate(
            range(0, n_rows - config.window_size + 1, config.step_size)
        )
    ]


def direction_key(source: str, target: str) -> str:
    return f"{source}_to_{target}"


def reference_filename(source: str, target: str) -> str:
    return f"norm_heatmap_data_{source}_to_{target}.csv"


def get_best_e_tau(
    data_window: pd.DataFrame,
    variable: str,
    config: TDCCMConfig = DEFAULT_CONFIG,
) -> tuple[int, int, float]:
    """Choose the embedding dimension and tau with the best simplex rho."""

    EDM = require_pyedm()
    lib_range = f"1 {len(data_window)}"
    pred_range = f"1 {len(data_window)}"
    best_rho = -float("inf")
    best_e: int | None = None
    best_tau: int | None = None

    for tau in config.tau_values:
        result = EDM.EmbedDimension(
            dataFrame=data_window,
            columns=variable,
            target=variable,
            lib=lib_range,
            pred=pred_range,
            maxE=config.max_embedding_dim,
            Tp=config.embedding_tp,
            tau=tau,
            exclusionRadius=config.exclusion_radius,
            validLib=[],
            numProcess=config.num_processes,
            showPlot=False,
        )
        if result.empty or result["rho"].isna().all():
            continue
        row = result.loc[result["rho"].idxmax()]
        rho = float(row["rho"])
        if rho > best_rho:
            best_rho = rho
            best_e = int(row["E"])
            best_tau = int(tau)

    if best_e is None or best_tau is None:
        raise ValueError(f"Could not determine E/tau for {variable}.")
    return best_e, best_tau, best_rho


def _run_directional_ccm(
    data_window: pd.DataFrame,
    source: str,
    target: str,
    embedding_dim: int,
    tau: int,
    tp: int,
    config: TDCCMConfig,
) -> float:
    """Run one directional CCM and return the maximum rho across library sizes."""

    max_lib_size = compute_max_lib_size(len(data_window), embedding_dim, tau, tp)
    if max_lib_size < config.lib_sizes_min:
        return 0.0

    EDM = require_pyedm()
    lib_sizes = f"{config.lib_sizes_min} {int(max_lib_size)} {config.lib_sizes_step}"
    result = EDM.CCM(
        dataFrame=data_window,
        columns=source,
        target=target,
        E=int(embedding_dim),
        Tp=int(tp),
        tau=int(tau),
        exclusionRadius=config.exclusion_radius,
        libSizes=lib_sizes,
        sample=config.sample,
        seed=config.seed,
        includeData=False,
        verbose=False,
        showPlot=False,
        returnObject=False,
    )
    column = f"{source}:{target}"
    if column not in result:
        raise KeyError(f"Expected CCM result column {column!r}; got {list(result.columns)!r}.")
    return float(result[column].max())


def run_tdccm_window(
    data_window: pd.DataFrame,
    window_id: int,
    pair: PairConfig,
    config: TDCCMConfig = DEFAULT_CONFIG,
) -> dict[str, list[dict[str, float | int]]]:
    """Run TDCCM over all configured `Tp` values for one window."""

    e1, tau1, _ = get_best_e_tau(data_window, pair.variable1, config)
    e2, tau2, _ = get_best_e_tau(data_window, pair.variable2, config)

    rows_1_to_2: list[dict[str, float | int]] = []
    rows_2_to_1: list[dict[str, float | int]] = []
    for tp in config.tp_values:
        rows_1_to_2.append(
            {
                "Window": window_id,
                "Tp": int(tp),
                "rho": _run_directional_ccm(
                    data_window,
                    pair.variable1,
                    pair.variable2,
                    e1,
                    tau1,
                    tp,
                    config,
                ),
            }
        )
        rows_2_to_1.append(
            {
                "Window": window_id,
                "Tp": int(tp),
                "rho": _run_directional_ccm(
                    data_window,
                    pair.variable2,
                    pair.variable1,
                    e2,
                    tau2,
                    tp,
                    config,
                ),
            }
        )

    return {
        direction_key(pair.variable1, pair.variable2): rows_1_to_2,
        direction_key(pair.variable2, pair.variable1): rows_2_to_1,
    }


def run_tdccm_pair(
    data: pd.DataFrame,
    pair: PairConfig,
    config: TDCCMConfig = DEFAULT_CONFIG,
    output_dir: Path | None = None,
) -> dict[str, pd.DataFrame]:
    """Run the full paper-parity TDCCM sweep for one pair."""

    results: dict[str, list[dict[str, float | int]]] = {
        direction_key(pair.variable1, pair.variable2): [],
        direction_key(pair.variable2, pair.variable1): [],
    }

    for window_id, start, end in window_slices(len(data), config):
        window = data.iloc[start:end].reset_index(drop=True)
        window_results = run_tdccm_window(window, window_id, pair, config)
        for key, rows in window_results.items():
            results[key].extend(rows)

    frames = {key: pd.DataFrame(rows, columns=["Window", "Tp", "rho"]) for key, rows in results.items()}
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        frames[direction_key(pair.variable1, pair.variable2)].to_csv(
            output_dir / reference_filename(pair.variable1, pair.variable2),
            index=False,
        )
        frames[direction_key(pair.variable2, pair.variable1)].to_csv(
            output_dir / reference_filename(pair.variable2, pair.variable1),
            index=False,
        )
    return frames


def with_runtime_overrides(
    config: TDCCMConfig = DEFAULT_CONFIG,
    *,
    num_processes: int | None = None,
    sample: int | None = None,
    seed: int | None = None,
) -> TDCCMConfig:
    """Return a config with CLI-safe runtime overrides applied."""

    updates: dict[str, int] = {}
    if num_processes is not None:
        updates["num_processes"] = num_processes
    if sample is not None:
        updates["sample"] = sample
    if seed is not None:
        updates["seed"] = seed
    return replace(config, **updates)


def compute_surrogate_ccm_convergence(
    data_window: pd.DataFrame,
    source: str,
    target: str,
    source_e: int,
    source_tau: int,
    source_tp: int,
    target_e: int,
    target_tau: int,
    target_tp: int,
    config: TDCCMConfig = DEFAULT_CONFIG,
) -> dict[str, dict[str, np.ndarray | pd.Series]]:
    """Compute the 95% surrogate quantile curves used for convergence checks."""

    EDM = require_pyedm()

    def _direction(
        shuffled_column: str,
        ccm_source: str,
        ccm_target: str,
        embedding_dim: int,
        tau: int,
        tp: int,
        seed_offset: int,
    ) -> tuple[pd.Series, np.ndarray]:
        surrogate_rhos: list[np.ndarray] = []
        lib_sizes: pd.Series | None = None
        max_lib_size = compute_max_lib_size(len(data_window), embedding_dim, tau, tp)
        lib_sizes_str = f"{config.lib_sizes_min} {int(max_lib_size)} {config.lib_sizes_step}"
        for idx in range(config.num_surrogates):
            surrogate = data_window.copy()
            rng = np.random.default_rng(config.seed + seed_offset + idx)
            surrogate[shuffled_column] = rng.permutation(surrogate[shuffled_column].to_numpy())
            result = EDM.CCM(
                dataFrame=surrogate,
                columns=ccm_source,
                target=ccm_target,
                E=int(embedding_dim),
                Tp=int(tp),
                tau=int(tau),
                exclusionRadius=config.exclusion_radius,
                libSizes=lib_sizes_str,
                sample=config.sample,
                seed=config.seed + seed_offset + idx,
                includeData=False,
                verbose=False,
                showPlot=False,
                returnObject=False,
            )
            if lib_sizes is None:
                lib_sizes = result["LibSize"]
            surrogate_rhos.append(result[f"{ccm_source}:{ccm_target}"].to_numpy())
        if lib_sizes is None:
            raise ValueError("No surrogate CCM results were generated.")
        return lib_sizes, np.percentile(np.asarray(surrogate_rhos), 95, axis=0)

    source_lib, source_quantile = _direction(
        source, source, target, source_e, source_tau, source_tp, 0
    )
    target_lib, target_quantile = _direction(
        target,
        target,
        source,
        target_e,
        target_tau,
        target_tp,
        config.num_surrogates,
    )
    return {
        direction_key(source, target): {"LibSize": source_lib, "Quantile95": source_quantile},
        direction_key(target, source): {"LibSize": target_lib, "Quantile95": target_quantile},
    }
