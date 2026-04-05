from __future__ import annotations

import os
import random
from typing import Dict, Optional

from src.core.board import TriangleBoard
from src.core.move import apply_move
from src.core.utils import get_all_moves_for_player, next_player
from src.ai.utils import MovePath, clone_board
from src.ml.model_loader import load_model, predict_advantage_proba

# global cache
_LOADED = None # model loaded 
_LOADED_PATH: Optional[str] = None 
_WARNED_MISSING = False

def _get_model(model_path: str):
    '''Load the ML model from the given path, with caching. \n
    Returns the loaded model or None if loading failed.'''
    global _LOADED, _LOADED_PATH, _WARNED_MISSING

    model_path = os.path.abspath(model_path)

    if not os.path.exists(model_path):
        if not _WARNED_MISSING:
            print(f"[ml_ai] Model not found: {model_path}. Falling back to random.")
            _WARNED_MISSING = True
        return None

    if _LOADED is not None and _LOADED_PATH == model_path:
        return _LOADED

    _LOADED = load_model(model_path)
    _LOADED_PATH = model_path
    return _LOADED


def _score_from_proba(proba: Dict[int, float], player: int) -> float:
    '''Convert the model's predicted probability distribution over advantage_player into a score for the given player. \n
     The score is higher if the model predicts a higher probability of advantage for `player` and lower if it predicts a higher probability for opponents.'''
    p_self = float(proba.get(player, 0.0))
    p_best_enemy = max((float(proba.get(p, 0.0)) for p in (1, 2, 3) if p != player), default=0.0)
    return p_self - p_best_enemy


def choose_ml_move(
    board: TriangleBoard,
    player: int,
    mode: str,
    *,
    model_path: str = os.path.join("models", "advantage_model.joblib"),
) -> Optional[MovePath]:
    """Choose a move using a trained ML model.

    The model predicts `advantage_player` (0=tie, 1..3=player) from a board state.
    We score each legal move by the resulting state's probability of favoring `player`.
    """
    if mode != "ml":
        raise ValueError(f"Invalid mode for choose_ml_move: {mode}")

    moves = get_all_moves_for_player(board, player)
    if not moves:
        return None

    loaded = _get_model(model_path)
    if loaded is None:
        return random.choice(moves)

    best_move: Optional[MovePath] = None
    best_score = float("-inf")

    for move in moves:
        sim = clone_board(board)
        apply_move(sim, move)

        w = sim.check_winner()
        if w == player:
            return move

        proba = predict_advantage_proba(loaded, board=sim.board, turn=next_player(player))
        if not proba:
            continue

        score = _score_from_proba(proba, player)
        if score > best_score:
            best_score = score
            best_move = move

    # If proba wasn't available for any reason, fall back.
    return best_move or random.choice(moves)
