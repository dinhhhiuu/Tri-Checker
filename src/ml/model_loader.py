from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


try:
	import joblib
	import numpy as np
except Exception as e:  # pragma: no cover
	raise SystemExit(
		"Missing ML dependencies. Install with: pip install -r requirements.txt\n"
		f"Original error: {e}"
	)


Board = List[List[int]] # board [[1], [0, 2], [3, 0, 0], ...]


@dataclass(frozen=True)
class LoadedModel:
	model: object
	metadata: Dict[str, object]


def load_model(path: str) -> LoadedModel:
	'''Load a trained model and its metadata from a file.'''
	bundle = joblib.load(path)
	if not isinstance(bundle, dict) or "model" not in bundle or "metadata" not in bundle:
		raise ValueError("Invalid model bundle format")
	return LoadedModel(model=bundle["model"], metadata=bundle["metadata"])


def _positions_from_metadata(metadata: Dict[str, object]) -> List[Tuple[int, int]]:
	'''Extract the list of board cell positions from model metadata. \n
	return: [(0,0), (0,1), (1,0), ...]'''
	positions = metadata.get("positions")
	if not isinstance(positions, list):
		raise ValueError("Model metadata missing positions")
	out: List[Tuple[int, int]] = []
	for item in positions:
		if (
			isinstance(item, (list, tuple))
			and len(item) == 2
			and isinstance(item[0], int)
			and isinstance(item[1], int)
		):
			out.append((int(item[0]), int(item[1])))
	if not out:
		raise ValueError("Model metadata positions invalid")
	return out


def featurize_one(board: Board, *, turn: int, metadata: Dict[str, object]) -> np.ndarray:
	'''Convert a single board state and turn into a feature vector for the model. \n'''
	positions = _positions_from_metadata(metadata)
	include_turn = bool(metadata.get("include_turn", False))

	n_cells = len(positions)
	base_dim = n_cells * 3
	turn_dim = 3 if include_turn else 0
	dim = base_dim + turn_dim

	x = np.zeros((1, dim), dtype=np.float32)
	for cell_index, (r, c) in enumerate(positions):
		v = int(board[r][c])
		if v in (1, 2, 3):
			x[0, cell_index * 3 + (v - 1)] = 1.0

	if include_turn and turn in (1, 2, 3):
		x[0, base_dim + (turn - 1)] = 1.0
	return x


def predict_advantage_player(
	loaded: LoadedModel,
	*,
	board: Board,
	turn: int,
) -> int:
	'''Predict the player with advantage (0=tie, 1..3=player) for the given board state and turn using the loaded model.'''
	x = featurize_one(board, turn=turn, metadata=loaded.metadata)
	model = loaded.model
	if not hasattr(model, "predict"):
		raise TypeError("Loaded model does not support predict()")
	pred = model.predict(x)
	return int(pred[0])


def predict_advantage_proba(
	loaded: LoadedModel,
	*,
	board: Board,
	turn: int,
) -> Optional[Dict[int, float]]:
	'''Predict the probability distribution over advantage_player (0=tie, 1..3=player) 
	for the given board state and turn using the loaded model. \n'''
	x = featurize_one(board, turn=turn, metadata=loaded.metadata)
	model = loaded.model
	if not hasattr(model, "predict_proba"):
		return None
	proba = model.predict_proba(x)[0] # proba for each class in model.classes_ [0.2, 0.2, 0.6]
	classes = getattr(model, "classes_", None) # class labels [1, 2, 3]
	if classes is None:
		return None
	return {int(c): float(p) for c, p in zip(classes, proba)} # {1: 0.2, 2: 0.2, 3: 0.6}
