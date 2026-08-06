from __future__ import annotations

import json
import os

from app import paper_simulator as sim
from app import probability_model as pm
from scripts.calibrate_decision_strategy import WALK_FORWARD_FOLDS, WALK_FORWARD_WINDOW_DAYS, _walk_forward_folds
from scripts.compare_recommendations import DEFAULT_SYMBOLS, _load_prepared, _symbols


def _samples_in_range(prepared: dict, benchmark: dict | None, start: int, end: int) -> tuple[list[list[float]], list[int]]:
    features_rows: list[list[float]] = []
    labels: list[int] = []
    for data in prepared.values():
        history = data["history"]
        limit = min(end, len(history) - 5)
        for i in range(start, limit):
            features = sim.feature_vector(data, i, benchmark)
            if features is None:
                continue
            price = float(history["close"].iloc[i])
            forward_return = (float(history["close"].iloc[i + 5]) / price - 1) * 100
            features_rows.append(features)
            labels.append(1 if forward_return > 0.5 else 0)
    return features_rows, labels


def main() -> None:
    symbols = _symbols() or DEFAULT_SYMBOLS
    prepared, benchmark, skipped = _load_prepared(symbols)
    max_len = min(len(data["history"]) for data in prepared.values())
    folds = _walk_forward_folds(max_len, WALK_FORWARD_FOLDS, WALK_FORWARD_WINDOW_DAYS, min_start=65)
    if len(folds) < 2:
        raise SystemExit("Historico insuficiente para separar pelo menos 2 janelas (treino + holdout).")

    *train_folds, holdout_fold = folds
    train_x: list[list[float]] = []
    train_y: list[int] = []
    for start, end in train_folds:
        features_rows, labels = _samples_in_range(prepared, benchmark, start, end)
        train_x += features_rows
        train_y += labels
    holdout_x, holdout_y = _samples_in_range(prepared, benchmark, *holdout_fold)

    model = pm.fit(sim.FEATURE_NAMES, train_x, train_y)

    holdout_predictions = [pm.predict_proba(model, features) for features in holdout_x]
    if holdout_y:
        holdout_hits = sum(1 for pred, actual in zip(holdout_predictions, holdout_y) if (pred >= 0.5) == bool(actual))
        model["holdout_accuracy"] = round(holdout_hits / len(holdout_y), 4)
        model["holdout_positive_rate"] = round(sum(holdout_y) / len(holdout_y), 4)
    else:
        model["holdout_accuracy"] = None
        model["holdout_positive_rate"] = None
    model["holdout_samples"] = len(holdout_y)
    model["train_folds"] = [{"start_index": start, "end_index": end} for start, end in train_folds]
    model["holdout_fold"] = {"start_index": holdout_fold[0], "end_index": holdout_fold[1]}
    model["symbols"] = sorted(prepared)
    model["skipped"] = skipped

    pm.save_model(model)
    pm.record_training(model)
    summary = {key: value for key, value in model.items() if key not in ("weights", "mean", "std")}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nModelo salvo em {os.getenv('PROBABILITY_MODEL_PATH', str(pm.MODEL_PATH))}")


if __name__ == "__main__":
    main()
