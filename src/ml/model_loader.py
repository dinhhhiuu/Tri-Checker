from __future__ import annotations

import pickle
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Tuple

from src.core.board import TriangleBoard

_PLAYERS = (1, 2, 3)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_MODEL_PATH = _PROJECT_ROOT / "models" / "triangle_win_model.pkl"


def get_default_model_path() -> Path:
    return _DEFAULT_MODEL_PATH


def _count_captures(board: TriangleBoard, row: int, col: int, player: int) -> int:
    capture_count = 0
    for path in board.get_all_moves(row, col):
        for (prev_r, prev_c), (curr_r, curr_c) in zip(path, path[1:]):
            if abs(curr_r - prev_r) == 2 or abs(curr_c - prev_c) == 2:
                mid_r = (prev_r + curr_r) // 2
                mid_c = (prev_c + curr_c) // 2
                mid_piece = board.board[mid_r][mid_c]
                if mid_piece not in (0, player):
                    capture_count += 1
    return capture_count


def _progress_value(board: TriangleBoard, player: int, row: int, col: int) -> float:
    scale = max(board.size - 1, 1)
    if player == 1:
        return row / scale
    if player == 2:
        return ((board.size - 1 - row) + col) / (2.0 * scale)
    return ((board.size - 1 - row) + (row - col)) / (2.0 * scale)


def board_to_features(board: TriangleBoard, turn: int) -> List[float]:
    """Encode board cells plus engineered tactical summary features for each player."""
    flat = [float(cell) / 3.0 for row in board.board for cell in row]
    pieces_by_player = {player: board.get_all_pieces(player) for player in _PLAYERS}
    piece_counts = {player: len(pieces) for player, pieces in pieces_by_player.items()}

    summary: List[float] = []
    for player in _PLAYERS:
        pieces = pieces_by_player[player]
        advancement = 0.0
        center_control = 0.0
        row_average = 0.0
        frontline_pieces = 0.0

        for row, col in pieces:
            progress = _progress_value(board, player, row, col)
            advancement += progress
            center_control += 1.0 / (1.0 + abs((row / 2.0) - col))
            row_average += row / max(board.size - 1, 1)
            if progress >= 0.55:
                frontline_pieces += 1.0

        piece_count = piece_counts[player]
        avg_advancement = advancement / piece_count if piece_count else 0.0
        avg_center = center_control / piece_count if piece_count else 0.0
        avg_row = row_average / piece_count if piece_count else 0.0
        frontline_ratio = frontline_pieces / piece_count if piece_count else 0.0

        summary.extend(
            [
                1.0 if piece_count > 0 else 0.0,
                piece_count / 10.0,
                avg_advancement,
                avg_center,
                avg_row,
                frontline_ratio,
            ]
        )

    for player in _PLAYERS:
        own_count = piece_counts[player]
        opponent_count = sum(piece_counts[other] for other in _PLAYERS if other != player)
        summary.append((own_count - (opponent_count / 2.0)) / 10.0)

    turn_features = [1.0 if turn == player else 0.0 for player in _PLAYERS]
    return flat + summary + turn_features


@lru_cache(maxsize=2)
def _load_payload(model_path: str) -> Optional[dict]:
    path = Path(model_path)
    if not path.exists():
        return None

    with path.open("rb") as fh:
        return pickle.load(fh)


def model_available(model_path: Optional[str | Path] = None) -> bool:
    path = Path(model_path) if model_path is not None else _DEFAULT_MODEL_PATH
    return path.exists()


def predict_winner_proba(
    board: TriangleBoard,
    turn: int,
    model_path: Optional[str | Path] = None,
) -> Optional[Tuple[float, float, float]]:
    """Return predicted win probabilities for players 1..3, or None if no model exists."""
    path = Path(model_path) if model_path is not None else _DEFAULT_MODEL_PATH
    payload = _load_payload(str(path))
    if payload is None:
        return None

    model = payload["model"]
    classes = list(payload.get("classes", getattr(model, "classes_", _PLAYERS)))

    try:
        probabilities = model.predict_proba([board_to_features(board, turn)])[0]
    except Exception:
        return None

    class_to_prob = {int(cls): float(prob) for cls, prob in zip(classes, probabilities)}
    result = tuple(class_to_prob.get(player, 0.0) for player in _PLAYERS)

    total = sum(result)
    if total <= 0:
        return None

    return tuple(value / total for value in result)
