from src.core.board import TriangleBoard
from typing import List, Tuple

MovePath = List[Tuple[int, int]]

def next_player(player: int) -> int:
    return 1 if player == 3 else player + 1

def get_all_moves_for_player(board: TriangleBoard, player: int) -> List[MovePath]:
    moves = []
    pieces = board.get_all_pieces(player)

    for (r, c) in pieces:
        paths = board.get_all_moves(r, c)
        moves.extend(paths)

    return moves