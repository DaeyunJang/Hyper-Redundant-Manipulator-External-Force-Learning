"""Evaluate aligned XYZ forces, threshold load state, and conditional location.

Forces enter in N and retain their recorded signs. ``pred_load`` is the state
derived from predicted force and the configured per-axis bands. It is distinct
from the auxiliary load head. Original ``true_id`` is never relabelled: only
the *evaluation* end-to-end target becomes 0 on true unloaded rows. Location
accuracy uses true loaded rows with known IDs, regardless of predicted load.
The tip task's constant conditional ID18 is a task constraint, not evidence
that a classifier learned contact location.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


AXES = ("fx", "fy", "fz")
FORCE_COLUMNS = [f"{kind}_{axis}_N" for kind in ("true", "pred") for axis in AXES]
REQUIRED_COLUMNS = FORCE_COLUMNS + [
    "true_load", "pred_load", "true_id", "pred_id", "conditional_pred_id"
]


def _divide(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else float("nan")


def _binary(values: pd.Series, name: str) -> np.ndarray:
    """Parse actual binary values; missing or the string 'False' is not true."""
    boolean_strings = {"True": 1, "False": 0, "true": 1, "false": 0}
    parsed = values.map(lambda value: boolean_strings.get(value, value))
    parsed = pd.to_numeric(parsed, errors="coerce").to_numpy(dtype=float)
    if not np.isin(parsed, [0, 1]).all():
        raise ValueError(f"{name} must contain only known binary labels 0/1")
    return parsed.astype(bool)


def _validated(df: pd.DataFrame) -> tuple[np.ndarray, ...]:
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing prediction columns: {sorted(missing)}")
    forces = df[FORCE_COLUMNS].to_numpy(dtype=float)
    if not np.isfinite(forces).all():
        raise ValueError("Force evaluation requires finite targets and predictions")
    true_load = _binary(df["true_load"], "true_load")
    pred_load = _binary(df["pred_load"], "pred_load")
    true_id = pd.to_numeric(df["true_id"], errors="coerce").to_numpy(dtype=float)
    pred_id = pd.to_numeric(df["pred_id"], errors="coerce").to_numpy(dtype=float)
    conditional_id = pd.to_numeric(
        df["conditional_pred_id"], errors="coerce"
    ).to_numpy(dtype=float)
    if not np.isin(pred_id, np.arange(19)).all():
        raise ValueError("pred_id must be an integer in 0..18")
    if not np.isin(conditional_id, np.arange(1, 19)).all():
        raise ValueError("conditional_pred_id must be an integer in 1..18")
    return forces[:, :3], forces[:, 3:], true_load, pred_load, true_id, pred_id, conditional_id


def _force_metrics(error: np.ndarray, prefix: str = "") -> dict[str, float | int]:
    result: dict[str, float | int] = {f"{prefix}n_samples": len(error)}
    if len(error):
        mae = np.mean(np.abs(error), axis=0)
        rmse = np.sqrt(np.mean(error ** 2, axis=0))
        bias = np.mean(error, axis=0)
        norm = np.linalg.norm(error, axis=1)
        scalar = {
            "force_mae": float(np.mean(np.abs(error))),
            "force_rmse": float(np.sqrt(np.mean(error ** 2))),
            "vector_mae": float(np.mean(norm)),
            "vector_rmse": float(np.sqrt(np.mean(norm ** 2))),
            "vector_p95_error": float(np.percentile(norm, 95)),
        }
    else:
        mae = rmse = bias = np.full(3, np.nan)
        scalar = dict.fromkeys(
            ("force_mae", "force_rmse", "vector_mae", "vector_rmse", "vector_p95_error"),
            float("nan"),
        )
    for axis_index, axis in enumerate(AXES):
        for metric, values in (("mae", mae), ("rmse", rmse), ("bias", bias)):
            scalar[f"{axis}_{metric}"] = float(values[axis_index])
    for key, value in scalar.items():
        result[f"{prefix}{key}_N"] = value
        result[f"{prefix}{key}_mN"] = value * 1000.0
    return result


def _load_metrics(
    true: np.ndarray, predicted: np.ndarray, prefix: str
) -> dict[str, float | int]:
    tp = int(np.sum(true & predicted))
    tn = int(np.sum(~true & ~predicted))
    fp = int(np.sum(~true & predicted))
    fn = int(np.sum(true & ~predicted))
    return {
        f"{prefix}tp": tp,
        f"{prefix}tn": tn,
        f"{prefix}fp": fp,
        f"{prefix}fn": fn,
        f"{prefix}precision": _divide(tp, tp + fp),
        f"{prefix}recall": _divide(tp, tp + fn),
        f"{prefix}f1": _divide(2 * tp, 2 * tp + fp + fn),
        f"{prefix}accuracy": _divide(tp + tn, len(true)),
        f"{prefix}false_positive_rate": _divide(fp, fp + tn),
        f"{prefix}false_negative_rate": _divide(fn, fn + tp),
    }


def evaluate_predictions(df: pd.DataFrame) -> dict[str, float | int]:
    """Return scalar metrics. Bias is prediction minus target; undefined is NaN.

    ``force_rmse`` is the root mean squared error across all XYZ components;
    ``vector_rmse`` is sqrt(mean(||pred-true||_2**2)), hence sqrt(3) times
    ``force_rmse``. ``vector_mae`` is mean Euclidean error, not magnitude-only
    error. Loaded/unloaded subsets follow true load labels, never predictions.
    """
    true_force, pred_force, true_load, pred_load, true_id, pred_id, conditional_id = _validated(df)
    error = pred_force - true_force
    metrics = _force_metrics(error)
    metrics.update(_force_metrics(error[true_load], "loaded_"))
    metrics.update(_force_metrics(error[~true_load], "unloaded_"))
    metrics.update(_load_metrics(true_load, pred_load, "load_"))
    if "load_head_pred" in df:
        head_pred = _binary(df["load_head_pred"], "load_head_pred")
        metrics.update(_load_metrics(true_load, head_pred, "load_head_"))
    else:
        metrics["load_head_f1"] = float("nan")

    known_id = np.isin(true_id, np.arange(1, 19))
    location_mask = true_load & known_id
    metrics["location_n_loaded"] = int(location_mask.sum())
    metrics["location_accuracy_loaded"] = _divide(
        np.sum(conditional_id[location_mask] == true_id[location_mask]), location_mask.sum()
    )
    metrics["location_gated_accuracy_loaded"] = _divide(
        np.sum(pred_id[location_mask] == true_id[location_mask]), location_mask.sum()
    )
    end_to_end_mask = ~true_load | known_id
    expected_id = np.where(true_load, true_id, 0)
    metrics["end_to_end_n_samples"] = int(end_to_end_mask.sum())
    metrics["end_to_end_id_accuracy"] = _divide(
        np.sum(pred_id[end_to_end_mask] == expected_id[end_to_end_mask]),
        end_to_end_mask.sum(),
    )
    return metrics


def _confusion(df: pd.DataFrame, conditional: bool = False) -> pd.DataFrame:
    _, _, true_load, _, true_id, pred_id, conditional_id = _validated(df)
    known_id = np.isin(true_id, np.arange(1, 19))
    if conditional:
        mask = true_load & known_id
        labels = list(range(1, 19))
        truth, prediction = true_id[mask], conditional_id[mask]
    else:
        mask = ~true_load | known_id
        labels = list(range(19))
        truth, prediction = np.where(true_load, true_id, 0)[mask], pred_id[mask]
    matrix = np.zeros((len(labels), len(labels)), dtype=np.int64)
    offset = labels[0]
    np.add.at(matrix, (truth.astype(int) - offset, prediction.astype(int) - offset), 1)
    result = pd.DataFrame(matrix, index=labels, columns=[f"pred_id_{i}" for i in labels])
    result.index.name = "true_evaluation_id"
    return result


def _force_bins(df: pd.DataFrame) -> pd.DataFrame:
    true_force = df[[f"true_{axis}_N" for axis in AXES]].to_numpy(dtype=float)
    magnitude_mN = np.linalg.norm(true_force, axis=1) * 1000.0
    bins = [0.0, 100.0, 250.0, 500.0, 1000.0, 2000.0, float("inf")]
    rows = []
    for lower, upper in zip(bins[:-1], bins[1:]):
        selected = df.loc[(magnitude_mN >= lower) & (magnitude_mN < upper)]
        rows.append({
            "true_force_norm_lower_mN_inclusive": lower,
            "true_force_norm_upper_mN_exclusive": upper,
            **evaluate_predictions(selected),
        })
    return pd.DataFrame(rows)


def _session_parts(df: pd.DataFrame) -> list[tuple[str, np.ndarray, list[np.ndarray]]]:
    """Allocate independent session coordinates and split plotted gaps.

    Session records retain source-row order. Lines break at missing rows,
    non-increasing time, and time gaps > 1.5 * the session median positive dt.
    Timestamps are subtracted as int64 before conversion to seconds.
    """
    parts = []
    groups = df.groupby("session_id", sort=False, dropna=False) if "session_id" in df else [("data", df)]
    offset = 0.0
    for name, original_group in groups:
        group = original_group.sort_values("source_row", kind="stable") if "source_row" in df else original_group
        positions = group["_plot_position"].to_numpy(dtype=int)
        if "elapsed_s" in group and np.isfinite(group["elapsed_s"].to_numpy(dtype=float)).all():
            time = group["elapsed_s"].to_numpy(dtype=float)
        elif "source_time_ns" in group:
            stamp = group["source_time_ns"].to_numpy(dtype=np.int64)
            time = (stamp - stamp[0]).astype(float) / 1e9
        else:
            time = np.arange(len(group), dtype=float)
        dt = np.diff(time)
        positive_dt = dt[dt > 0]
        typical_dt = float(np.median(positive_dt)) if len(positive_dt) else 1.0
        breaks = (dt <= 0) | (dt > 1.5 * typical_dt)
        if "source_row" in group:
            breaks |= np.diff(group["source_row"].to_numpy(dtype=np.int64)) != 1
        segments = np.split(np.arange(len(group)), np.flatnonzero(breaks) + 1)
        # A single-session figure keeps the original elapsed_s scale.
        plot_time = time if len(parts) == 0 else time - time.min() + offset
        offset = float(plot_time.max()) + max(typical_dt * 10, 1.0)
        parts.append((str(name), plot_time, [positions[part] for part in segments]))
    return parts


def _plot_predictions(df: pd.DataFrame, outdir: Path, task: str) -> None:
    if df.empty:
        return
    data = df.copy()
    data["_plot_position"] = np.arange(len(data))
    parts = _session_parts(data)
    # Map times to source row positions; indexing remains valid with repeated pandas indices.
    x = np.empty(len(data), dtype=float)
    for _, time, segments in parts:
        x[np.concatenate(segments)] = time
    true_force = data[[f"true_{axis}_N" for axis in AXES]].to_numpy(dtype=float) * 1000.0
    pred_force = data[[f"pred_{axis}_N" for axis in AXES]].to_numpy(dtype=float) * 1000.0
    fig, axes = plt.subplots(3, 1, figsize=(14, 8), sharex=True)
    for axis_index, ax in enumerate(axes):
        first = True
        for _, _, segments in parts:
            for segment in segments:
                # Decimation is for rendering only; evaluation always uses every sample.
                stride = max(1, int(np.ceil(len(segment) / 5000)))
                rows = segment[::stride]
                marker = "." if len(rows) == 1 else None
                ax.plot(x[rows], true_force[rows, axis_index], color="black", lw=0.9,
                        alpha=0.7, marker=marker, label="Aligned target" if first else None)
                ax.plot(x[rows], pred_force[rows, axis_index], color="tab:blue", lw=0.9,
                        alpha=0.85, marker=marker, label="Prediction" if first else None)
                first = False
        ax.set_ylabel(f"{AXES[axis_index]} [mN]")
        ax.grid(alpha=0.2)
        if len(parts) > 1:
            for _, time, _ in parts[1:]:
                ax.axvline(time[0], color="gray", lw=0.6, ls="--")
    axes[0].legend(loc="upper right")
    axes[0].set_title(f"{task}: recorded aligned sign; {len(parts)} session(s)")
    axes[-1].set_xlabel("Elapsed time [s]" if len(parts) == 1 else "Concatenated session time [s]; dashed lines = session starts")
    fig.tight_layout()
    fig.savefig(outdir / "force_timeseries.png", dpi=140)
    plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(14, 5), sharex=True)
    true_load = _binary(data["true_load"], "true_load").astype(float)
    pred_load = _binary(data["pred_load"], "pred_load").astype(float)
    probability = data["load_probability"].to_numpy(dtype=float) if "load_probability" in data else None
    first = True
    for _, _, segments in parts:
        for segment in segments:
            rows = segment[::max(1, int(np.ceil(len(segment) / 5000)))]
            marker = "." if len(rows) == 1 else None
            axes[0].plot(x[rows], true_load[rows], color="black", lw=0.9,
                         marker=marker, label="True load" if first else None)
            axes[0].plot(x[rows], pred_load[rows], color="tab:orange", lw=0.9,
                         marker=marker, alpha=0.7, label="Force-band prediction" if first else None)
            if probability is not None:
                axes[1].plot(x[rows], probability[rows], color="tab:green", lw=0.9,
                             marker=marker, label="Auxiliary load probability" if first else None)
            first = False
    for ax in axes:
        ax.set_ylim(-0.05, 1.05)
        ax.grid(alpha=0.2)
        if ax.lines:
            ax.legend(loc="upper right")
    axes[0].set_ylabel("Loaded = 1")
    axes[1].set_ylabel("Probability")
    axes[1].set_xlabel("Elapsed time [s]" if len(parts) == 1 else "Concatenated session time [s]")
    axes[0].set_title(f"{task}: threshold state and auxiliary head are reported separately")
    fig.tight_layout()
    fig.savefig(outdir / "load_timeseries.png", dpi=140)
    plt.close(fig)


def save_evaluation(df: pd.DataFrame, outdir: str | Path, task: str) -> dict[str, float | int]:
    """Save metric tables, two ID confusion matrices, and force/load plots.

    ``metrics.csv`` has one row for straightforward model-table concatenation.
    ``per_id_metrics.csv`` groups by unchanged original experiment ID.
    ``confusion.csv`` includes threshold load errors and unloaded target ID0;
    ``conditional_confusion.csv`` evaluates location on true loaded rows only.
    JSON encodes undefined metrics as null (valid JSON), CSV as blank values.
    """
    metrics = evaluate_predictions(df)
    destination = Path(outdir)
    destination.mkdir(parents=True, exist_ok=True)
    serializable: dict[str, Any] = {
        name: value if np.isfinite(value) else None for name, value in metrics.items()
    }
    (destination / "metrics.json").write_text(
        json.dumps(serializable, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    pd.DataFrame([metrics]).to_csv(destination / "metrics.csv", index=False)
    rows = []
    for true_id, group in df.groupby("true_id", dropna=False, sort=True):
        rows.append({"true_id": true_id, **evaluate_predictions(group)})
    pd.DataFrame(rows, columns=["true_id", *metrics]).to_csv(destination / "per_id_metrics.csv", index=False)
    _confusion(df).to_csv(destination / "confusion.csv")
    _confusion(df, conditional=True).to_csv(destination / "conditional_confusion.csv")
    _force_bins(df).to_csv(destination / "error_by_force.csv", index=False)
    _plot_predictions(df, destination, task)
    return metrics
