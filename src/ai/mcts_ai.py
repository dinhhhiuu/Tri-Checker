from __future__ import annotations

from typing import List, Optional, Tuple

from src.core.board import TriangleBoard

MovePath = List[Tuple[int, int]]

def get_all_moves_for_player(board: TriangleBoard, player: int) -> List[MovePath]:
    pass

def choose_mcts_move(board: TriangleBoard, player: int, mode: str) -> Optional[MovePath]:
    if mode != "mcts":
        raise ValueError(f"Invalid mode for choose_mcts_move: {mode}")
    return None