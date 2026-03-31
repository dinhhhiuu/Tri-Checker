from __future__ import annotations

from typing import List, Optional, Tuple

from src.core.board import TriangleBoard

MovePath = List[Tuple[int, int]]

def get_all_moves_for_player(board: TriangleBoard, player: int) -> List[MovePath]:
    pass

def choose_minimax_move(board: TriangleBoard, player: int, mode: str) -> Optional[MovePath]:
    if mode != "minimax":
        raise ValueError(f"Invalid mode for choose_minimax_move: {mode}")
    return None
