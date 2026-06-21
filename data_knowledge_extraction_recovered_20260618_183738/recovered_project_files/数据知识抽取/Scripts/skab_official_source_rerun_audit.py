from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import platform
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from skab_official_repository_baseline_audit import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SKAB_REPO,
    EXPECTED_OUTLIER_LEADERBOARD,
    _best_frame_for_series,
    _fs_path,
    _load_data_frames,
    _metrics_from_records,
    _sha256,
    _write_json,
    _write_jsonl,
    _write_text,
)


VERSION = "skab-official-source-rerun-audit-v1"
RECORD_DIR_NAME = "skab_official_source_rerun_records"
DELTA_AUDIT_FILENAME = "skab_source_rerun_delta_audit.json"
PRESERVED_SOURCE_RERUN_NOTE = (
    "Preserved from a prior pinned official Python 3.10/TensorFlow source rerun because the current process cannot rerun this method."
)
MSCRED_COMPATIBILITY_PATCH_NOTE = (
    "Minimal Keras call-signature compatibility patch applied; architecture and threshold logic unchanged."
)
MSCRED_COMPATIBILITY_PATCH_DETAIL = (
    "TensorFlow/Keras 2.15 passes a training kwarg into the official custom attention layer; "
    "the rerun uses a minimal signature-compatibility wrapper and leaves the architecture, hyperparameters, "
    "signature-matrix construction, and threshold policy unchanged."
)

SOURCE_METHODS = {
    "T2": {
        "notebook": "t2_SKAB.ipynb",
        "core_module": "core.t2",
        "requires": ["numpy", "pandas", "scipy", "sklearn", "matplotlib"],
        "tensorflow_required": False,
        "external_dependency": None,
    },
    "T2-q": {
        "notebook": "t2_with_q_SKAB.ipynb",
        "core_module": "core.t2",
        "requires": ["numpy", "pandas", "scipy", "sklearn", "matplotlib"],
        "tensorflow_required": False,
        "external_dependency": None,
    },
    "Isolation_Forest": {
        "notebook": "isolation_forest.ipynb",
        "core_module": "core.Isolation_Forest",
        "requires": ["numpy", "pandas", "sklearn", "tensorflow"],
        "tensorflow_required": True,
        "external_dependency": None,
    },
    "MSET": {
        "notebook": "MSET.ipynb",
        "core_module": "core.MSET",
        "requires": ["numpy", "pandas", "scipy", "sklearn", "tensorflow"],
        "tensorflow_required": True,
        "external_dependency": None,
    },
    "Conv_AE": {
        "notebook": "Conv_AE.ipynb",
        "core_module": "core.Conv_AE",
        "requires": ["numpy", "pandas", "tensorflow"],
        "tensorflow_required": True,
        "external_dependency": None,
    },
    "LSTM_AE": {
        "notebook": "LSTM_AE.ipynb",
        "core_module": "core.LSTM_AE",
        "requires": ["numpy", "pandas", "tensorflow"],
        "tensorflow_required": True,
        "external_dependency": None,
    },
    "MSCRED": {
        "notebook": "mscred.ipynb",
        "core_module": "core.MSCRED",
        "requires": ["numpy", "pandas", "tensorflow"],
        "tensorflow_required": True,
        "external_dependency": None,
    },
    "Vanilla_AE": {
        "notebook": "Vanilla_AE.ipynb",
        "core_module": "core.Vanilla_AE",
        "requires": ["numpy", "pandas", "tensorflow"],
        "tensorflow_required": True,
        "external_dependency": None,
    },
    "Vanilla_LSTM": {
        "notebook": "Vanilla_LSTM.ipynb",
        "core_module": "core.Vanilla_LSTM",
        "requires": ["numpy", "pandas", "tensorflow"],
        "tensorflow_required": True,
        "external_dependency": None,
    },
    "Arima_anomaly_detection": {
        "notebook": "ArimaFD.ipynb",
        "core_module": None,
        "requires": ["numpy", "pandas", "arimafd"],
        "tensorflow_required": False,
        "external_dependency": "arimafd",
    },
}


def _module_present(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _read_text(path: Path) -> str:
    if not os.path.exists(_fs_path(path)):
        return ""
    with open(_fs_path(path), "r", encoding="utf-8") as handle:
        return handle.read()


def _read_json(path: Path) -> dict[str, Any]:
    if not os.path.exists(_fs_path(path)):
        return {}
    with open(_fs_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def _source_rerun_delta_audit_status(output_dir: Path, unmatched_methods: list[str]) -> dict[str, Any]:
    unmatched = sorted(str(method) for method in unmatched_methods)
    audit_path = output_dir / DELTA_AUDIT_FILENAME
    payload = _read_json(audit_path)
    gates = payload.get("gates") if isinstance(payload.get("gates"), dict) else {}
    covered_methods = sorted(str(method) for method in payload.get("covered_delta_methods", []))
    missing_delta_methods = sorted(str(method) for method in payload.get("missing_delta_methods", unmatched))
    expected_methods_covered = set(unmatched).issubset(set(covered_methods))
    explained = (
        not unmatched
        or (
            bool(payload)
            and payload.get("status") == "source_rerun_delta_profile_complete"
            and not missing_delta_methods
            and expected_methods_covered
            and bool(gates.get("deltas_attributed_to_predictions"))
        )
    )
    return {
        "audit_file": DELTA_AUDIT_FILENAME,
        "audit_present": bool(payload),
        "status": payload.get("status"),
        "unmatched_methods": unmatched,
        "covered_delta_methods": covered_methods,
        "missing_delta_methods": [] if not unmatched else missing_delta_methods,
        "gates": gates,
        "explained": bool(explained),
        "claim_boundary": payload.get(
            "claim_boundary",
            "No source-rerun delta audit is available; unmatched source reruns remain unexplained.",
        ),
    }


def _python_constraint_status(pyproject_text: str) -> dict[str, Any]:
    required = ">=3.10,<3.11" if 'python = ">=3.10,<3.11"' in pyproject_text else None
    current = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    compatible = sys.version_info.major == 3 and sys.version_info.minor == 10 if required else None
    return {
        "declared_constraint": required,
        "current_python": current,
        "implementation": platform.python_implementation(),
        "compatible": compatible,
    }


@contextmanager
def _official_notebook_context(skab_repo: Path):
    old_cwd = Path.cwd()
    old_path = list(sys.path)
    os.chdir(str((skab_repo / "notebooks").absolute()))
    sys.path.insert(0, str(skab_repo.absolute()))
    try:
        yield
    finally:
        sys.path[:] = old_path
        os.chdir(str(old_cwd.absolute()))


def _records_from_predictions(
    method: str,
    predictions: list[pd.Series],
    frames: list[tuple[Path, pd.DataFrame]],
    skab_repo: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    alignment_rows: list[dict[str, Any]] = []
    for series_index, series in enumerate(predictions):
        source_path, frame, overlap = _best_frame_for_series(series, frames)
        pred_series = pd.Series(
            np.nan_to_num(np.asarray(series), nan=0.0),
            index=pd.to_datetime(series.index).astype(str),
        )
        aligned = frame[frame["_datetime_key"].isin(pred_series.index)].copy()
        y_pred = aligned["_datetime_key"].map(pred_series).fillna(0.0).to_numpy(dtype=float)
        rel_source = str(source_path.relative_to(skab_repo / "data")).replace("\\", "/")
        alignment_rows.append(
            {
                "series_index": int(series_index),
                "source_file": rel_source,
                "series_rows": int(len(series)),
                "matched_rows": int(len(aligned)),
                "overlap_rows": int(overlap),
            }
        )
        for row_index, (_, row) in enumerate(aligned.iterrows()):
            run_id = rel_source.replace("/", "_").replace(".csv", "")
            sample_index = int(row.name) if isinstance(row.name, (int, np.integer)) else row_index
            pred = int(float(y_pred[row_index]) > 0.0)
            true = int(float(row.get("anomaly", 0.0)) > 0.0)
            records.append(
                {
                    "row_index": int(len(records)),
                    "record_id": f"official_skab_source_{method}_{run_id}_{sample_index:05d}",
                    "method": method,
                    "source_file": rel_source,
                    "datetime": str(row["datetime"]),
                    "y_true_original": true,
                    "y_pred_original": pred,
                    "positive_score": float(pred),
                    "positive_threshold": 0.5,
                    "run_id": run_id,
                    "sample_index": sample_index,
                    "run_group": str(source_path.parent.name),
                    "anomaly": true,
                    "changepoint": int(float(row.get("changepoint", 0.0)) > 0.0),
                }
            )
    return records, alignment_rows


def _run_official_t2_family(method: str, skab_repo: Path) -> list[pd.Series]:
    with _official_notebook_context(skab_repo):
        from core.t2 import T2
        from core.utils import load_preprocess_skab

        using_pca = method == "T2-q"
        model = T2(scaling=True, using_pca=using_pca)
        predictions: list[pd.Series] = []
        for X_train, X_test, _y_train, _y_test in load_preprocess_skab():
            model.fit(X_train)
            model.predict(X_test, window_size=5, plot_fig=False)
            if using_pca:
                prediction = pd.Series(
                    ((model.t2["T2"].values > model.t2_ucl) | (model.q["Q"] > model.q_ucl)).astype(int),
                    index=X_test.index,
                ).fillna(0)
            else:
                prediction = pd.Series(
                    (model.t2["T2"].values > (2 * model.t2_ucl)).astype(int),
                    index=X_test.index,
                ).fillna(0)
            predictions.append(prediction)
        return predictions


def _run_official_isolation_forest(skab_repo: Path) -> list[pd.Series]:
    with _official_notebook_context(skab_repo):
        from core.Isolation_Forest import Isolation_Forest
        from core.utils import load_preprocess_skab

        model = Isolation_Forest([0, -1, 0.0005])
        predictions: list[pd.Series] = []
        for X_train, X_test, _y_train, _y_test in load_preprocess_skab():
            model.fit(X_train)
            prediction = (
                pd.Series(model.predict(X_test) * -1, index=X_test.index)
                .rolling(3)
                .median()
                .fillna(0)
                .replace(-1, 0)
            )
            predictions.append(prediction)
        return predictions


def _movmean(array: np.ndarray, window: int) -> np.ndarray:
    n = np.size(array)
    xx = array.copy()
    windows = []
    for i in range(0, window):
        windows.append(np.roll(xx.tolist() + [np.nan] * window, i))
    averaged = np.nanmean(windows, axis=0)
    window_ceil = math.ceil(window / 2)
    return averaged[window_ceil - 1 : n + window_ceil - 1]


def _run_official_mset(skab_repo: Path) -> list[pd.Series]:
    with _official_notebook_context(skab_repo):
        from core.MSET import MSET
        from core.utils import load_preprocess_skab

        predictions: list[pd.Series] = []
        for X_train, X_test, _y_train, _y_test in load_preprocess_skab():
            model = MSET()
            model.fit(X_train)
            y_pred = model.predict(X_test)
            error = np.linalg.norm(X_test - y_pred, axis=1)
            relative_error = _movmean(error / np.linalg.norm(y_pred, axis=1), window=60)
            prediction = (
                pd.DataFrame((relative_error > 0.01), X_test.index)
                .fillna(0)
                .any(axis=1)
                .astype(int)
            )
            predictions.append(prediction)
        return predictions


def _run_official_vanilla_ae(skab_repo: Path) -> list[pd.Series]:
    with _official_notebook_context(skab_repo):
        from sklearn.preprocessing import StandardScaler

        from core.Vanilla_AE import Vanilla_AE
        from core.utils import load_preprocess_skab

        best_params = [5, 4, 2, 0.005, 32]
        quantile = 0.99
        model = Vanilla_AE(best_params)
        predictions: list[pd.Series] = []
        for X_train, X_test, _y_train, _y_test in load_preprocess_skab():
            scaler = StandardScaler()
            scaler.fit(X_train)
            model.fit(scaler.transform(X_train))
            residuals_train = (
                pd.DataFrame(scaler.transform(X_train) - model.predict(scaler.transform(X_train)))
                .abs()
                .sum(axis=1)
            )
            ucl = residuals_train.quantile(quantile) * 5 / 2
            x_test_scaled = scaler.transform(X_test)
            residuals_test = pd.DataFrame(x_test_scaled - model.predict(x_test_scaled)).abs().sum(axis=1)
            prediction = pd.Series((residuals_test > ucl).astype(int).values, index=X_test.index).fillna(0)
            predictions.append(prediction)
        return predictions


def _run_official_conv_ae(skab_repo: Path) -> list[pd.Series]:
    with _official_notebook_context(skab_repo):
        from sklearn.preprocessing import StandardScaler

        from core.Conv_AE import Conv_AE
        from core.utils import create_sequences, load_preprocess_skab

        n_steps = 60
        quantile = 0.999
        model = Conv_AE()
        predictions: list[pd.Series] = []
        for X_train, X_test, _y_train, _y_test in load_preprocess_skab():
            scaler = StandardScaler()
            scaler.fit(X_train)
            x_train_seq = create_sequences(scaler.transform(X_train), n_steps)
            model.fit(x_train_seq)
            residuals = pd.Series(
                np.sum(np.mean(np.abs(x_train_seq - model.predict(x_train_seq)), axis=1), axis=1)
            )
            ucl = residuals.quantile(quantile) * 4 / 3
            x_test_seq = create_sequences(scaler.transform(X_test), n_steps)
            test_residuals = pd.Series(
                np.sum(np.mean(np.abs(x_test_seq - model.predict(x_test_seq)), axis=1), axis=1)
            )
            anomalous_data = test_residuals > ucl
            anomalous_indices: list[int] = []
            for data_idx in range(n_steps - 1, len(x_test_seq) - n_steps + 1):
                if np.all(anomalous_data[data_idx - n_steps + 1 : data_idx]):
                    anomalous_indices.append(data_idx)
            prediction = pd.Series(data=0, index=X_test.index)
            prediction.iloc[anomalous_indices] = 1
            predictions.append(prediction)
        return predictions


def _run_official_lstm_ae(skab_repo: Path) -> list[pd.Series]:
    with _official_notebook_context(skab_repo):
        from sklearn.preprocessing import StandardScaler

        from core.LSTM_AE import LSTM_AE
        from core.utils import create_sequences, load_preprocess_skab

        epochs = 100
        batch_size = 32
        val_split = 0.1
        n_steps = 10
        quantile = 0.99
        model = LSTM_AE([epochs, batch_size, val_split])
        predictions: list[pd.Series] = []
        for X_train, X_test, _y_train, _y_test in load_preprocess_skab():
            scaler = StandardScaler()
            scaler.fit(X_train)
            x_train_seq = create_sequences(scaler.transform(X_train), n_steps)
            model.fit(x_train_seq)
            residuals = pd.Series(
                np.sum(np.mean(np.abs(x_train_seq - model.predict(x_train_seq)), axis=1), axis=1)
            )
            ucl = residuals.quantile(quantile) * 3 / 2
            x_test_seq = create_sequences(scaler.transform(X_test), n_steps)
            test_residuals = pd.Series(
                np.sum(np.mean(np.abs(x_test_seq - model.predict(x_test_seq)), axis=1), axis=1)
            )
            anomalous_data = test_residuals > ucl
            anomalous_indices: list[int] = []
            for data_idx in range(n_steps - 1, len(x_test_seq) - n_steps + 1):
                if np.all(anomalous_data[data_idx - n_steps + 1 : data_idx]):
                    anomalous_indices.append(data_idx)
            prediction = pd.Series(data=0, index=X_test.index)
            prediction.iloc[anomalous_indices] = 1
            predictions.append(prediction)
        return predictions


def _create_mscred_dataset(
    df: pd.DataFrame,
    win_size: list[int],
    gap_time: int,
    step_max: int,
) -> np.ndarray:
    from sklearn.preprocessing import MinMaxScaler

    data = np.array(df, dtype=np.float64)
    sensor_n = data.shape[1]
    scale_n = len(win_size)
    data = MinMaxScaler().fit_transform(data).T
    data_all: list[list[np.ndarray]] = []
    for win in win_size:
        matrix_all: list[np.ndarray] = []
        for t in range(win_size[-1], len(df), gap_time):
            matrix_t = np.zeros((sensor_n, sensor_n))
            for i in range(sensor_n):
                for j in range(i, sensor_n):
                    matrix_t[i][j] = np.inner(data[i, t - win : t], data[j, t - win : t]) / win
                    matrix_t[j][i] = matrix_t[i][j]
            matrix_all.append(matrix_t)
        data_all.append(matrix_all)
    data_stacked = np.transpose(np.asarray(data_all), (1, 2, 3, 0))
    dataset = np.stack(
        [data_stacked[start : start + step_max] for start in range(0, len(data_stacked) - step_max + 1)],
        axis=0,
    )
    return dataset.reshape([-1, step_max, sensor_n, sensor_n, scale_n])


def _run_official_mscred(skab_repo: Path) -> list[pd.Series]:
    with _official_notebook_context(skab_repo):
        from core.MSCRED import MSCRED
        from core.utils import load_preprocess_skab

        class CompatibleMSCRED(MSCRED):
            def attention(self, outputs, koef, **_kwargs):
                return super().attention(outputs, koef)

        step_max = 10
        gap_time = 1
        win_size = [5, 10, 30]
        scale_n = len(win_size)
        quantile = 0.99
        predictions: list[pd.Series] = []
        for X_train, X_test, _y_train, _y_test in load_preprocess_skab():
            sensor_n = X_train.shape[1]
            x_train_sig = _create_mscred_dataset(X_train, win_size, gap_time, step_max)
            x_test_sig = _create_mscred_dataset(X_test, win_size, gap_time, step_max)
            model = CompatibleMSCRED([sensor_n, scale_n, step_max])
            model.fit(x_train_sig, x_train_sig[:, -1])
            x_pred = model.predict(x_test_sig) * -1
            resid_mat = x_test_sig[:, -1] - x_pred
            mse = np.mean(np.square(resid_mat), axis=(1, 2))
            index = X_test.index[win_size[-1] :: gap_time][step_max - 1 :]
            mse_df = pd.DataFrame(mse, index=index, columns=[f"win_{i}" for i in win_size])
            ucl = mse_df.quantile(quantile) * 2 / 3
            prediction = pd.DataFrame((mse_df > ucl), index).fillna(0).any(axis=1).astype(int)
            predictions.append(prediction)
        return predictions


def _split_sequences(sequences: np.ndarray, n_steps: int) -> tuple[np.ndarray, np.ndarray]:
    x_rows: list[np.ndarray] = []
    y_rows: list[np.ndarray] = []
    for i in range(len(sequences)):
        end_ix = i + n_steps
        if end_ix > len(sequences) - 1:
            break
        x_rows.append(sequences[i:end_ix, :])
        y_rows.append(sequences[end_ix, :])
    return np.asarray(x_rows), np.asarray(y_rows)


def _run_official_vanilla_lstm(skab_repo: Path) -> list[pd.Series]:
    with _official_notebook_context(skab_repo):
        from sklearn.preprocessing import StandardScaler

        from core.Vanilla_LSTM import Vanilla_LSTM
        from core.utils import load_preprocess_skab

        n_steps = 5
        epochs = 25
        batch_size = 32
        val_split = 0.2
        quantile = 0.99
        model = Vanilla_LSTM([n_steps, epochs, batch_size, val_split])
        predictions: list[pd.Series] = []
        for X_train, X_test, _y_train, _y_test in load_preprocess_skab():
            scaler = StandardScaler()
            scaler.fit(X_train)
            x_train, y_train = _split_sequences(scaler.transform(X_train), n_steps)
            model.fit(x_train, y_train)
            residuals_train = pd.DataFrame(y_train - model.predict(x_train)).abs().sum(axis=1)
            ucl = residuals_train.quantile(quantile) * 5
            x_test, y_test = _split_sequences(scaler.transform(X_test), n_steps)
            residuals_test = pd.DataFrame(y_test - model.predict(x_test)).abs().sum(axis=1)
            prediction = pd.Series(
                (residuals_test > ucl).astype(int).values,
                index=X_test[n_steps:].index,
            ).fillna(0)
            predictions.append(prediction)
        return predictions


def _run_official_method(method: str, skab_repo: Path) -> list[pd.Series]:
    if method in {"T2", "T2-q"}:
        return _run_official_t2_family(method, skab_repo)
    if method == "Isolation_Forest":
        return _run_official_isolation_forest(skab_repo)
    if method == "MSET":
        return _run_official_mset(skab_repo)
    if method == "Vanilla_AE":
        return _run_official_vanilla_ae(skab_repo)
    if method == "Conv_AE":
        return _run_official_conv_ae(skab_repo)
    if method == "LSTM_AE":
        return _run_official_lstm_ae(skab_repo)
    if method == "MSCRED":
        return _run_official_mscred(skab_repo)
    if method == "Vanilla_LSTM":
        return _run_official_vanilla_lstm(skab_repo)
    raise ValueError(f"No source rerun implementation for {method}")


def _method_dependency_status(method: str, skab_repo: Path) -> dict[str, Any]:
    spec = SOURCE_METHODS[method]
    missing = [name for name in spec["requires"] if not _module_present(name)]
    notebook_path = skab_repo / "notebooks" / str(spec["notebook"])
    core_module = spec["core_module"]
    core_importable = None
    core_import_error = None
    if core_module:
        try:
            with _official_notebook_context(skab_repo):
                __import__(str(core_module))
            core_importable = True
        except Exception as exc:  # pragma: no cover - diagnostic path
            core_importable = False
            core_import_error = f"{type(exc).__name__}: {exc}"
    return {
        "method": method,
        "notebook": spec["notebook"],
        "notebook_present": notebook_path.exists(),
        "core_module": core_module,
        "core_importable": core_importable,
        "core_import_error": core_import_error,
        "requires": spec["requires"],
        "missing_dependencies": missing,
        "tensorflow_required": spec["tensorflow_required"],
        "external_dependency": spec["external_dependency"],
        "runnable_in_current_env": notebook_path.exists() and not missing and (core_importable is not False),
    }


def _source_rerun_row(
    method: str,
    skab_repo: Path,
    output_dir: Path,
    frames: list[tuple[Path, pd.DataFrame]],
    *,
    materialize_records: bool,
) -> dict[str, Any]:
    predictions = _run_official_method(method, skab_repo)
    records, alignment_rows = _records_from_predictions(method, predictions, frames, skab_repo)
    metrics = _metrics_from_records(records)
    expected = EXPECTED_OUTLIER_LEADERBOARD[method]
    metric_deltas = {
        "f1": abs(metrics["f1"] - float(expected["f1"])),
        "far_percent": abs(metrics["far_percent"] - float(expected["far_percent"])),
        "mar_percent": abs(metrics["mar_percent"] - float(expected["mar_percent"])),
    }
    matches_expected = (
        metric_deltas["f1"] <= 0.01
        and metric_deltas["far_percent"] <= 0.5
        and metric_deltas["mar_percent"] <= 0.5
    )
    record_file: Path | None = None
    record_sha: str | None = None
    if materialize_records:
        record_file = output_dir / RECORD_DIR_NAME / f"{method}.jsonl"
        _write_jsonl(record_file, records)
        record_sha = _sha256(record_file)
    row = {
        "method": method,
        "notebook": SOURCE_METHODS[method]["notebook"],
        "core_module": SOURCE_METHODS[method]["core_module"],
        "source_rerun_status": "source_rerun_complete",
        "n_prediction_series": int(len(predictions)),
        "n_prediction_records": int(len(records)),
        "all_series_aligned": all(
            int(row["series_rows"]) == int(row["matched_rows"]) == int(row["overlap_rows"])
            for row in alignment_rows
        ),
        "metrics": metrics,
        "expected_leaderboard": expected,
        "metric_deltas_from_expected": metric_deltas,
        "leaderboard_match_tolerance": {"f1": 0.01, "far_percent": 0.5, "mar_percent": 0.5},
        "matches_expected_leaderboard": matches_expected,
        "record_file": str(record_file.relative_to(output_dir)) if record_file else None,
        "record_sha256": record_sha,
        "claim_boundary": "Official SKAB notebook/core logic rerun for this method only; not a full official leaderboard source rerun.",
    }
    if method == "MSCRED":
        row["compatibility_patch"] = MSCRED_COMPATIBILITY_PATCH_DETAIL
        row["claim_boundary"] += f" {MSCRED_COMPATIBILITY_PATCH_NOTE}"
    return row


def _preserved_existing_source_rows(
    output_dir: Path,
    *,
    skip_methods: set[str],
) -> list[dict[str, Any]]:
    existing = _read_json(output_dir / "skab_official_source_rerun_audit.json")
    preserved: list[dict[str, Any]] = []
    for row in existing.get("source_rerun_rows", []):
        if not isinstance(row, dict):
            continue
        method = str(row.get("method"))
        if method in skip_methods or method not in set(SOURCE_METHODS):
            continue
        record_file = row.get("record_file")
        record_sha = row.get("record_sha256")
        if not record_file or not record_sha:
            continue
        record_path = output_dir / str(record_file)
        if not os.path.exists(_fs_path(record_path)) or _sha256(record_path) != record_sha:
            continue
        copied = dict(row)
        copied["preserved_from_existing_audit"] = True
        base_boundary = str(copied.get("claim_boundary") or "").replace(PRESERVED_SOURCE_RERUN_NOTE, "").strip()
        if method == "MSCRED":
            copied["compatibility_patch"] = copied.get("compatibility_patch") or MSCRED_COMPATIBILITY_PATCH_DETAIL
            if MSCRED_COMPATIBILITY_PATCH_NOTE not in base_boundary:
                base_boundary = f"{base_boundary} {MSCRED_COMPATIBILITY_PATCH_NOTE}".strip()
        copied["claim_boundary"] = f"{base_boundary} {PRESERVED_SOURCE_RERUN_NOTE}".strip()
        preserved.append(copied)
    return preserved


def build_skab_official_source_rerun_audit(
    skab_repo: Path | str = DEFAULT_SKAB_REPO,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    *,
    materialize_records: bool = True,
    only_methods: list[str] | None = None,
) -> dict[str, Any]:
    skab_repo = Path(skab_repo)
    output_dir = Path(output_dir)
    pyproject_text = _read_text(skab_repo / "pyproject.toml")
    dependency_rows = [_method_dependency_status(method, skab_repo) for method in SOURCE_METHODS]
    dependency_by_method = {row["method"]: row for row in dependency_rows}
    frames = _load_data_frames(skab_repo) if skab_repo.exists() else []
    source_rerun_rows: list[dict[str, Any]] = []
    source_rerun_errors: list[dict[str, str]] = []
    python_status = _python_constraint_status(pyproject_text)
    if only_methods is not None:
        candidate_methods = list(only_methods)
    else:
        candidate_methods = ["T2", "T2-q"]
        if bool(python_status.get("compatible")):
            candidate_methods.extend(
                method
                for method in [
                    "Isolation_Forest",
                    "MSET",
                    "Vanilla_AE",
                    "Conv_AE",
                    "LSTM_AE",
                    "MSCRED",
                    "Vanilla_LSTM",
                ]
                if dependency_by_method.get(method, {}).get("runnable_in_current_env")
            )
    for method in candidate_methods:
        try:
            source_rerun_rows.append(
                _source_rerun_row(
                    method,
                    skab_repo,
                    output_dir,
                    frames,
                    materialize_records=materialize_records,
                )
            )
        except Exception as exc:  # pragma: no cover - diagnostic path
            source_rerun_errors.append({"method": method, "error": f"{type(exc).__name__}: {exc}"})
    successful_methods = {str(row["method"]) for row in source_rerun_rows}
    source_rerun_rows.extend(
        _preserved_existing_source_rows(
            output_dir,
            skip_methods=set(candidate_methods) | successful_methods,
        )
    )
    tensorflow_available = _module_present("tensorflow")
    arimafd_available = _module_present("arimafd")
    t2_rows = [row for row in source_rerun_rows if row["method"] in {"T2", "T2-q"}]
    lightweight_rows = [row for row in source_rerun_rows if row["method"] in {"Isolation_Forest", "MSET"}]
    tensorflow_deep_methods = {"Vanilla_AE", "Conv_AE", "LSTM_AE", "MSCRED", "Vanilla_LSTM"}
    deep_rows = [
        row
        for row in source_rerun_rows
        if row["method"] in tensorflow_deep_methods
    ]
    deep_matched_rows = [row for row in deep_rows if row["matches_expected_leaderboard"] and row["all_series_aligned"]]
    deep_by_method = {row["method"]: row for row in deep_rows}
    deep_rerun_complete = all(
        method in deep_by_method
        and deep_by_method[method]["all_series_aligned"]
        and deep_by_method[method]["record_file"]
        and deep_by_method[method]["record_sha256"]
        for method in tensorflow_deep_methods
    )
    unmatched_source_methods = sorted(
        str(row["method"])
        for row in source_rerun_rows
        if row.get("expected_leaderboard") and not bool(row.get("matches_expected_leaderboard"))
    )
    delta_audit = _source_rerun_delta_audit_status(output_dir, unmatched_source_methods)
    gates = {
        "official_skab_repository_extracted": skab_repo.exists(),
        "official_notebook_sources_present": all((skab_repo / "notebooks" / str(row["notebook"])).exists() for row in dependency_rows),
        "official_core_sources_present": (skab_repo / "core").exists(),
        "current_python_matches_official_constraint": bool(python_status.get("compatible")),
        "tensorflow_available_for_deep_official_notebooks": tensorflow_available,
        "arimafd_available_for_external_official_notebook": arimafd_available,
        "source_rerun_t2_family_recomputed": len(t2_rows) == 2
        and all(row["matches_expected_leaderboard"] and row["all_series_aligned"] for row in t2_rows),
        "source_rerun_tensorflow_lightweight_baselines_recomputed": len(lightweight_rows) == 2
        and all(row["matches_expected_leaderboard"] and row["all_series_aligned"] for row in lightweight_rows),
        "source_rerun_tensorflow_deep_baselines_partial": len(deep_matched_rows) >= 2,
        "source_rerun_frozen_records_materialized": bool(source_rerun_rows)
        and all(row["record_file"] and row["record_sha256"] for row in source_rerun_rows),
        "official_deep_notebooks_rerun_from_source": deep_rerun_complete,
        "source_rerun_leaderboard_deltas_explained": bool(delta_audit["explained"]),
        "official_notebooks_rerun_from_source": False,
    }
    missing = [name for name, value in gates.items() if not value]
    return {
        "version": VERSION,
        "status": "official_skab_source_rerun_audit_partial",
        "claim_boundary": (
            "This audit reruns implemented official SKAB notebook/core logic and records environment blockers for "
            "the remaining official notebooks. It is partial source-rerun evidence, not a complete official leaderboard rerun."
        ),
        "skab_repo": str(skab_repo),
        "python_status": python_status,
        "dependency_rows": dependency_rows,
        "source_rerun_rows": source_rerun_rows,
        "source_rerun_errors": source_rerun_errors,
        "unmatched_source_rerun_methods": unmatched_source_methods,
        "source_rerun_delta_audit": delta_audit,
        "record_dir": RECORD_DIR_NAME,
        "gates": gates,
        "missing_gates": missing,
        "next_actions": [
            "Use the pinned Python 3.10 official-SKAB environment with TensorFlow 2.15 for any TensorFlow source-rerun refresh.",
            "Resolve or formally scope out the unavailable arimafd dependency before making any ArimaFD official-source claim.",
            (
                "Keep LSTM-AE/MSCRED/Vanilla-LSTM source reruns as diagnostic frozen-record evidence: their row/label alignment deltas are explained "
                "at the prediction level, but they still do not match the official leaderboard within tolerance."
                if delta_audit["explained"]
                else "Do not flip the official notebook/source gate until ArimaFD is rerun or formally scoped out and the LSTM-AE/MSCRED/Vanilla-LSTM source rerun deltas are explained."
            ),
            "Keep the implemented official source reruns as partial provenance evidence, not as a full leaderboard-superiority claim.",
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# SKAB Official Source Rerun Audit",
        "",
        f"- Version: {payload['version']}",
        f"- Status: {payload['status']}",
        f"- Claim boundary: {payload['claim_boundary']}",
        f"- Python: {payload['python_status']['current_python']}",
        f"- Declared Python constraint: {payload['python_status']['declared_constraint']}",
        "",
        "## Gates",
        "",
        "| Gate | Status |",
        "|---|---:|",
    ]
    for gate, value in payload["gates"].items():
        lines.append(f"| {gate} | {'pass' if value else 'blocked'} |")
    lines.extend(
        [
            "",
            "## Source Rerun Rows",
            "",
            "| Method | Records | F1 | FAR | MAR | README match | Frozen record file | Boundary |",
            "|---|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for row in payload["source_rerun_rows"]:
        metrics = row["metrics"]
        lines.append(
            "| {method} | {records} | {f1:.4f} | {far:.2f} | {mar:.2f} | {match} | `{record}` | {boundary} |".format(
                method=row["method"],
                records=int(row["n_prediction_records"]),
                f1=float(metrics["f1"]),
                far=float(metrics["far_percent"]),
                mar=float(metrics["mar_percent"]),
                match="yes" if row["matches_expected_leaderboard"] else "no",
                record=row["record_file"] or "",
                boundary=row["claim_boundary"],
            )
        )
    delta_audit = payload.get("source_rerun_delta_audit") or {}
    lines.extend(
        [
            "",
            "## Source-Rerun Delta Audit",
            "",
            f"- Audit file: `{delta_audit.get('audit_file', DELTA_AUDIT_FILENAME)}`",
            f"- Status: {delta_audit.get('status') or 'missing'}",
            f"- Explained: {'yes' if delta_audit.get('explained') else 'no'}",
            "- Covered delta methods: "
            + (", ".join(str(method) for method in delta_audit.get("covered_delta_methods", [])) or "none"),
            f"- Claim boundary: {delta_audit.get('claim_boundary') or 'No source-rerun delta audit is available.'}",
        ]
    )
    if payload.get("unmatched_source_rerun_methods"):
        unmatched_explanation = (
            "These methods have frozen source-rerun records and row/label alignment deltas are explained at the prediction level; "
            "they still do not match the README leaderboard tolerance, so they remain diagnostic evidence."
            if delta_audit.get("explained")
            else "These methods have frozen source-rerun records but do not match the README leaderboard tolerance; they are diagnostic evidence until the deltas are explained."
        )
        lines.extend(
            [
                "",
                "## Unmatched Source Rerun Rows",
                "",
                unmatched_explanation,
                "",
            ]
        )
        for method in payload["unmatched_source_rerun_methods"]:
            lines.append(f"- {method}")
    lines.extend(
        [
            "",
            "## Dependency Readiness",
            "",
            "| Method | Notebook | Missing dependencies | Runnable now? |",
            "|---|---|---|---:|",
        ]
    )
    for row in payload["dependency_rows"]:
        missing = ", ".join(row["missing_dependencies"]) or "none"
        lines.append(
            f"| {row['method']} | `{row['notebook']}` | {missing} | {'yes' if row['runnable_in_current_env'] else 'no'} |"
        )
    lines.extend(["", "## Next Actions", ""])
    lines.extend(f"- {action}" for action in payload["next_actions"])
    lines.append("")
    return "\n".join(lines)


def write_skab_official_source_rerun_audit(
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    *,
    skab_repo: Path | str = DEFAULT_SKAB_REPO,
    only_methods: list[str] | None = None,
) -> list[Path]:
    output_dir = Path(output_dir)
    payload = build_skab_official_source_rerun_audit(
        skab_repo=skab_repo,
        output_dir=output_dir,
        only_methods=only_methods,
    )
    json_path = output_dir / "skab_official_source_rerun_audit.json"
    md_path = output_dir / "skab_official_source_rerun_audit.md"
    _write_json(json_path, payload)
    _write_text(md_path, render_markdown(payload))
    return [json_path, md_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Audit official SKAB notebook/core source rerun readiness.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--skab-repo", type=Path, default=DEFAULT_SKAB_REPO)
    parser.add_argument(
        "--methods",
        default=None,
        help="Optional comma-separated source methods to rerun; existing rows for other methods are preserved when possible.",
    )
    args = parser.parse_args(argv)
    only_methods = None
    if args.methods:
        only_methods = [method.strip() for method in str(args.methods).split(",") if method.strip()]
        unknown = sorted(set(only_methods) - set(SOURCE_METHODS))
        if unknown:
            raise SystemExit(f"Unknown source methods: {', '.join(unknown)}")
    for path in write_skab_official_source_rerun_audit(
        args.output_dir,
        skab_repo=args.skab_repo,
        only_methods=only_methods,
    ):
        print(path)


if __name__ == "__main__":
    main()
