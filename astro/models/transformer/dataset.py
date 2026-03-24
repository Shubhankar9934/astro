from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset


def load_fused_parquet(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path).sort_values("Date").reset_index(drop=True)
    return df


def compute_labels_direction(
    close: np.ndarray, horizon: int
) -> np.ndarray:
    """1 if forward return > 0 over horizon else 0. Last rows marked -1 (invalid)."""
    n = len(close)
    y = np.full(n, -1, dtype=np.int64)
    for i in range(n - horizon):
        r = close[i + horizon] / close[i] - 1.0
        y[i] = 1 if r > 0 else 0
    return y


class WindowDataset(Dataset):
    def __init__(
        self,
        df: pd.DataFrame,
        feature_columns: List[str],
        seq_len: int,
        horizon: int,
        mean: np.ndarray,
        std: np.ndarray,
        valid_indices: np.ndarray,
    ):
        self.df = df
        self.feature_columns = feature_columns
        self.seq_len = seq_len
        self.horizon = horizon
        self.mean = mean
        self.std = np.where(std < 1e-8, 1.0, std)
        self.valid_indices = valid_indices
        mat = df[feature_columns].to_numpy(dtype=np.float64)
        self._mat = mat
        close = df["close"].to_numpy(dtype=np.float64) if "close" in df.columns else df["Close"].to_numpy(dtype=np.float64)
        self._y = compute_labels_direction(close, horizon)

    def __len__(self) -> int:
        return len(self.valid_indices)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        end = int(self.valid_indices[idx])
        start = end - self.seq_len
        window = self._mat[start:end].copy()
        window = (window - self.mean) / self.std
        x = torch.from_numpy(window).float()
        y = int(self._y[end - 1])
        return x, torch.tensor(y, dtype=torch.long)


def train_val_split_indices(
    df: pd.DataFrame,
    close_col: str,
    seq_len: int,
    horizon: int,
    val_fraction: float = 0.15,
):
    n_rows = len(df)
    usable = np.arange(seq_len, n_rows - horizon + 1)
    close = df[close_col].to_numpy(dtype=np.float64)
    y = compute_labels_direction(close, horizon)
    mask = np.array([y[int(e) - 1] >= 0 for e in usable])
    usable = usable[mask]
    split = int(len(usable) * (1 - val_fraction))
    return usable[:split], usable[split:]


def fit_scaler(df: pd.DataFrame, feature_columns: List[str], train_idx: np.ndarray, seq_len: int):
    rows = []
    for end in train_idx:
        start = end - seq_len
        rows.append(df.iloc[start:end][feature_columns].to_numpy())
    stacked = np.concatenate(rows, axis=0)
    mean = stacked.mean(axis=0)
    std = stacked.std(axis=0)
    return mean, std


def save_scaler(path: Path, mean: np.ndarray, std: np.ndarray, columns: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, mean=mean, std=std, columns=np.array(columns))


def load_scaler(path: Path) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    z = np.load(path, allow_pickle=True)
    cols = [str(c) for c in z["columns"].tolist()]
    return z["mean"], z["std"], cols
