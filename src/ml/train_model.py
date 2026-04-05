from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


try:
	import joblib
	import numpy as np
	from sklearn.linear_model import LogisticRegression
	from sklearn.metrics import classification_report
	from sklearn.model_selection import train_test_split
except Exception as e:  # pragma: no cover
	raise SystemExit(
		"Missing ML dependencies. Install with: pip install -r requirements.txt\n"
		f"Original error: {e}"
	)


Board = List[List[int]]


@dataclass(frozen=True)
class Example:
	board: Board
	turn: int
	label: int # advantage_player (0=tie,1..3=player)


def iter_examples_jsonl(path: str, *, drop_ties: bool) -> Iterable[Example]:
	with open(path, "r", encoding="utf-8") as f:
		for line in f:
			line = line.strip()
			if not line:
				continue
			obj = json.loads(line)
			label = int(obj.get("advantage_player", 0))
			if drop_ties and label == 0:
				continue
			board = obj["board"]
			turn = int(obj["turn"])
			yield Example(board=board, turn=turn, label=label)
def load_dataset(path: str, *, drop_ties: bool) -> List[Example]:
	return list(iter_examples_jsonl(path, drop_ties=drop_ties))


def board_positions(board_size: int) -> List[Tuple[int, int]]:
	# TriangleBoard uses rows with length r+1.
	return [(r, c) for r in range(board_size) for c in range(r + 1)]


def infer_board_size(board: Board) -> int:
	return len(board)


def featurize(
	examples: Sequence[Example], # list (board, turn, label)
	*,
	board_size: int,
	include_turn: bool, 
) -> Tuple[np.ndarray, np.ndarray, Dict[str, object]]:
	"""
	Chuyển đổi dữ liệu thô (board state, turn, label) thành định dạng số (feature matrix X và label vector y).
	
	Return (X, y, metadata).

	Features (binary): 3 planes for players (p1/p2/p3) for each cell.
	Optionally append a 3-dim one-hot for `turn`.

	Ex: [0,0,1, 0,1,0, 1,0,0, 1,0,0] => [3, 2, 1] and turn for player 1 
	"""
	positions = board_positions(board_size) # (0,0), (1,0), (1,1), (2,0), (2,1), (2,2) ... up to board_size
	n_cells = len(positions) # 55 for board_size=10
	base_dim = n_cells * 3 # [0,0,0] for empty, [1,0,0] for p1, [0,1,0] for p2, [0,0,1] for p3: cờ ở mỗi cell
	turn_dim = 3 if include_turn else 0 # [0,0,0] if turn not in (1,2,3), else one-hot for current turn: lượt của ai
	dim = base_dim + turn_dim # tổng số features: 165 for board_size=10 without turn, 168 with turn

	# x: feature (input), y: label (output)
	X = np.zeros((len(examples), dim), dtype=np.float32) # mỗi hàng sẽ là 1 state của board
	y = np.zeros((len(examples),), dtype=np.int64) # label là ai có lợi thế nhất ở state đó (0=tie, 1..3=player)

	for i, ex in enumerate(examples):
		y[i] = int(ex.label) # thay label vào mảng y

		# board planes
		for cell_index, (r, c) in enumerate(positions):
			v = int(ex.board[r][c]) # value ở cell đó: 0=empty, 1=p1, 2=p2, 3=p3
			if v in (1, 2, 3):
				X[i, cell_index * 3 + (v - 1)] = 1.0 # vị trí bắt đầu là 0, 3, ... tại (1, 0, 0) là p1

		if include_turn:
			t = int(ex.turn)
			if t in (1, 2, 3):
				X[i, base_dim + (t - 1)] = 1.0

	# metadata for reference (not used in training)
	metadata: Dict[str, object] = {
		"board_size": board_size,
		"positions": positions,
		"include_turn": include_turn,
		"feature_dim": dim, # số chiều của feature (input) sau khi featurize, dùng để kiểm tra khi load model sau này
		"label_meaning": "advantage_player (0=tie,1..3=player)",
	}
	return X, y, metadata


def class_distribution(y: np.ndarray) -> Dict[int, int]:
	'''Count the number of samples for each class label in y.'''
	unique, counts = np.unique(y, return_counts=True)
	return {int(k): int(v) for k, v in zip(unique, counts)}


def train_classifier(
	X_train: np.ndarray,
	y_train: np.ndarray,
	*,
	seed: int,
	class_weight: object,
) -> LogisticRegression:
	'''
		Train a classifier (Logistic Regression) to predict advantage_player from features. \n
		Input X_train is the feature matrix, y_train is the label vector. \n
		Returns the trained model.
	'''
	# Multiclass logistic regression is a solid baseline for binary board features.
	# multiclass is handled automatically when labels have >2 classes.
	clf = LogisticRegression(
		solver="lbfgs", # good for small datasets, supports multiclass, and handles L2 regularization by default.
		max_iter=2000, # increase max_iter to ensure convergence on larger datasets.
		random_state=seed, # for reproducibility
		class_weight=class_weight, # handle class imbalance if specified (e.g., "balanced" to weight inversely proportional to class frequencies)
	)
	clf.fit(X_train, y_train)
	return clf 


def save_bundle(out_path: str, *, model: object, metadata: Dict[str, object]) -> None:
	'''Save the trained model and its metadata together in a single file.'''
	os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
	bundle = {"model": model, "metadata": metadata}
	joblib.dump(bundle, out_path)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
	p = argparse.ArgumentParser(description="Train an ML model on generated TriangleBoard data")
	p.add_argument(
		"--data",
		default="data/ml_dataset.jsonl",
		help="Path to dataset file (JSONL)",
	)
	p.add_argument(
		"--out-model",
		default="models/advantage_model.joblib",
		help="Where to save the trained model bundle",
	)
	p.add_argument("--drop-ties", action="store_true", help="Drop samples with advantage_player==0")
	p.add_argument("--include-turn", action="store_true", help="Include current turn as feature")
	p.add_argument("--test-size", type=float, default=0.2, help="Test split ratio")
	p.add_argument("--seed", type=int, default=123, help="Random seed")
	p.add_argument(
		"--class-weight",
		choices=["none", "balanced"],
		default="balanced",
		help="Handle imbalanced labels (default: balanced)",
	)
	return p.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
	args = parse_args(argv)
	if not os.path.exists(args.data):
		raise SystemExit(f"Dataset not found: {args.data}")

	examples = load_dataset(args.data, drop_ties=args.drop_ties)
	if not examples:
		raise SystemExit("No training examples loaded (check file/drop-ties).")

	board_size = infer_board_size(examples[0].board)
	X, y, metadata = featurize(examples, board_size=board_size, include_turn=bool(args.include_turn))
	metadata.update(
		{
			"input_path": os.path.abspath(args.data),
			"drop_ties": bool(args.drop_ties),
			"n_examples": int(len(examples)),
			# thống kê số lượng mẫu cho mỗi lớp (0=tie, 1..3=player) trong tập dữ liệu
			"class_distribution": class_distribution(y), 
			"seed": int(args.seed), 
		}
	)

	# Stratify when possible (needs >=2 samples per class)
	stratify = y
	dist = class_distribution(y)
	if any(v < 2 for v in dist.values()) or len(dist) < 2:
		stratify = None

	X_train, X_test, y_train, y_test = train_test_split(
		X,
		y,
		test_size=float(args.test_size),
		random_state=int(args.seed),
		stratify=stratify,
	)

	cw: object = None if args.class_weight == "none" else "balanced"
	model = train_classifier(X_train, y_train, seed=int(args.seed), class_weight=cw)
	y_pred = model.predict(X_test)

	# Print report (kept simple for terminal usage)
	print("Dataset:", args.data)
	print("Examples:", len(examples))
	print("Classes:", metadata["class_distribution"])
	print("Feature dim:", int(metadata["feature_dim"]))
	print("Model:", type(model).__name__)
	print("\nClassification report:\n")
	# precision/recall/f1 for each class, with 4 decimal places.
	print(classification_report(y_test, y_pred, digits=4, zero_division=0)) 
	save_bundle(args.out_model, model=model, metadata=metadata)
	print(f"Saved model -> {args.out_model}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
