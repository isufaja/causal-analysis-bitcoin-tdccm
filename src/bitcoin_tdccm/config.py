"""Shared paper-parity configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA = DATA_DIR / "raw" / "new_all_data2024.csv"
PROCESSED_DATED_DATA = DATA_DIR / "processed" / "DateTime_normalized_log_returns.csv"
PROCESSED_PYEDM_DATA = DATA_DIR / "processed" / "normalized_log_returns.csv"
REFERENCE_DIR = DATA_DIR / "reference"
FIGURES_DIR = PROJECT_ROOT / "figures"

ASSETS = ("BTC", "SPX", "GOLD")


@dataclass(frozen=True)
class PairConfig:
    """A directional pair analyzed in the paper."""

    name: str
    variable1: str
    variable2: str

    @property
    def reference_dir(self) -> Path:
        return REFERENCE_DIR / self.name


@dataclass(frozen=True)
class TDCCMConfig:
    """Parameters used for the paper-parity TDCCM run."""

    window_size: int = 100
    step_size: int = 30
    max_embedding_dim: int = 10
    embedding_tp: int = 1
    tau_values: tuple[int, ...] = (-3, -2, -1)
    tp_values: tuple[int, ...] = tuple(range(-10, 11))
    exclusion_radius: int = 0
    num_processes: int = 4
    sample: int = 100
    seed: int = 0
    lib_sizes_min: int = 15
    lib_sizes_step: int = 10
    num_surrogates: int = 100


DEFAULT_CONFIG = TDCCMConfig()

PAIRS: dict[str, PairConfig] = {
    "btc-spx": PairConfig("btc-spx", "BTC", "SPX"),
    "btc-gold": PairConfig("btc-gold", "BTC", "GOLD"),
}

# These filters reproduce the final paper figure notebook. They are intentionally
# named and centralized because they are manual paper-figure filters, not part of
# the raw TDCCM computation.
PAPER_FIGURE_FILTERS: dict[str, dict[str, tuple[int, ...]]] = {
    "btc-spx": {
        "BTC_to_SPX": (3, 4, 5, 6, 13, 14, 26, 30, 33, 45),
        "SPX_to_BTC": (0, 1, 2, 5, 10, 11, 12, 15, 16, 26, 27, 28, 45, 50),
    },
    "btc-gold": {
        "BTC_to_GOLD": (
            0,
            1,
            2,
            3,
            4,
            7,
            8,
            10,
            11,
            12,
            13,
            14,
            16,
            17,
            19,
            22,
            26,
            27,
            28,
            29,
            30,
            31,
            34,
            35,
            36,
            37,
            38,
            42,
            44,
            45,
            46,
            49,
            50,
            52,
        ),
        "GOLD_to_BTC": (
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            9,
            10,
            12,
            14,
            15,
            17,
            18,
            20,
            21,
            22,
            25,
            29,
            31,
            32,
            33,
            34,
            35,
            37,
            38,
            39,
            41,
            43,
            45,
            48,
            49,
            50,
            51,
            52,
        ),
    },
}
