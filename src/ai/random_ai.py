from __future__ import annotations

import random
from typing import List, Optional, Tuple

from src.core.board import TriangleBoard


MovePath = List[Tuple[int, int]]


def get_all_moves_for_player(board: TriangleBoard, player: int) -> List[MovePath]:
    moves: List[MovePath] = []
    for r in range(board.size):
        for c in range(r + 1):
            if board.board[r][c] != player:
                continue
            for path in board.get_all_moves(r, c):
                if len(path) >= 2:
                    moves.append(path)
    return moves


def choose_random_move(board: TriangleBoard, player: int, mode: str) -> Optional[MovePath]:
    if mode != "random":
        raise ValueError(f"Invalid mode for choose_random_move: {mode}")
    
    moves = get_all_moves_for_player(board, player)
    if not moves:
        return None
    return random.choice(moves)