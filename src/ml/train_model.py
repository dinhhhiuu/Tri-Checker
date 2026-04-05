from __future__ import annotations

import argparse
import pickle
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier, VotingClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.ml.model_loader import get_default_model_path


def _oversample_training_data(X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(42)
    unique, counts = np.unique(y, return_counts=True)
    target_count = int(counts.max())

    x_parts = []
    y_parts = []
    for cls in unique:
        X_cls = X[y == cls]
        extra = target_count - len(X_cls)
        if extra > 0:
            indices = rng.choice(len(X_cls), size=extra, replace=True)
            X_cls = np.concatenate([X_cls, X_cls[indices]], axis=0)
        x_parts.append(X_cls)
        y_parts.append(np.full(len(X_cls), cls, dtype=int))

    X_balanced = np.concatenate(x_parts, axis=0)
    y_balanced = np.concatenate(y_parts, axis=0)
    order = rng.permutation(len(X_balanced))
    return X_balanced[order], y_balanced[order]


def _candidate_models() -> Dict[str, object]:
    mlp = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "mlp",
                MLPClassifier(
                    hidden_layer_sizes=(128, 64, 32),
                    activation="relu",
                    alpha=5e-4,
                    learning_rate_init=7e-4,
                    max_iter=700,
                    random_state=42,
                    early_stopping=True,
                    validation_fraction=0.12,
                    n_iter_no_change=25,
                ),
            ),
        ]
    )

    ensemble = VotingClassifier(
        estimators=[
            (
                "mlp",
                Pipeline(
                    steps=[
                        ("scaler", StandardScaler()),
                        (
                            "mlp",
                            MLPClassifier(
                                hidden_layer_sizes=(128, 64),
                                activation="relu",
                                alpha=1e-3,
                                learning_rate_init=8e-4,
                                max_iter=600,
                                random_state=42,
                                early_stopping=True,
                            ),
                        ),
                    ]
                ),
            ),
            (
                "rf",
                RandomForestClassifier(
                    n_estimators=300,
                    max_depth=18,
                    min_samples_leaf=2,
                    class_weight="balanced_subsample",
                    n_jobs=-1,
                    random_state=42,
                ),
            ),
            (
                "et",
                ExtraTreesClassifier(
                    n_estimators=400,
                    max_depth=None,
                    min_samples_leaf=1,
                    class_weight="balanced",
                    n_jobs=-1,
                    random_state=42,
                ),
            ),
        ],
        voting="soft",
        weights=[3, 2, 2],
        n_jobs=1,
    )

    return {
        "deep_mlp": mlp,
        "soft_voting_ensemble": ensemble,
    }


def train_model(input_path: Path, output_path: Path) -> None:
    data = np.load(input_path)
    X = data["X"]
    y = data["y"]

    if len(X) < 10:
        raise ValueError("Dataset is too small; generate more self-play games first.")

    unique, counts = np.unique(y, return_counts=True)
    if len(unique) < 2:
        raise ValueError("Need at least 2 winner classes in the dataset to train a model.")

    can_stratify = np.all(counts >= 2)
    stratify = y if can_stratify else None

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=stratify,
    )

    X_train_balanced, y_train_balanced = _oversample_training_data(X_train, y_train)

    candidate_results = {}
    best_name = None
    best_model = None
    best_train_accuracy = -1.0
    best_test_accuracy = -1.0

    for name, model in _candidate_models().items():
        model.fit(X_train_balanced, y_train_balanced)
        train_accuracy = accuracy_score(y_train, model.predict(X_train))
        test_accuracy = accuracy_score(y_test, model.predict(X_test))

        candidate_results[name] = {
            "train_accuracy": float(train_accuracy),
            "test_accuracy": float(test_accuracy),
        }
        print(f"[{name}] train_accuracy={train_accuracy:.3f} test_accuracy={test_accuracy:.3f}")

        if test_accuracy > best_test_accuracy:
            best_name = name
            best_model = model
            best_train_accuracy = float(train_accuracy)
            best_test_accuracy = float(test_accuracy)

    if best_model is None or best_name is None:
        raise RuntimeError("No candidate model was successfully trained.")

    X_full_balanced, y_full_balanced = _oversample_training_data(X, y)
    best_model.fit(X_full_balanced, y_full_balanced)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as fh:
        pickle.dump(
            {
                "model": best_model,
                "classes": list(getattr(best_model, "classes_", unique)),
                "train_accuracy": best_train_accuracy,
                "test_accuracy": best_test_accuracy,
                "sample_count": int(len(X)),
                "feature_count": int(X.shape[1]),
                "model_name": best_name,
                "candidate_results": candidate_results,
            },
            fh,
        )

    print(f"Training samples: {len(X)}")
    print(f"Feature count: {X.shape[1]}")
    print(f"Winner classes: {list(unique)}")
    print(f"Best model: {best_name}")
    print(f"Train accuracy: {best_train_accuracy:.3f}")
    print(f"Test accuracy: {best_test_accuracy:.3f}")
    print(f"Saved model to {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a stronger ML model for Triangle Board state evaluation.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data") / "self_play_data.npz",
        help="Path to the .npz dataset generated by src.ml.generate_data.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=get_default_model_path(),
        help="Where to save the trained model.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    train_model(args.input, args.output)


if __name__ == "__main__":
    main()
