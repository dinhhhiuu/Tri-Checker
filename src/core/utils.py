from src.core.board import TriangleBoard
from typing import List, Tuple

MovePath = List[Tuple[int, int]]

def init_players(board: TriangleBoard) -> None:
    # Player 1 (top)
    for r in range(4):
        for c in range(r + 1):
            board._set_piece(r, c, 1)

    # Player 2 (bottom-left)
    for r in range(6, 10):
        for c in range(0, r - 5):
            board._set_piece(r, c, 2)

    # Player 3 (bottom-right)
    for r in range(6, 10):
        for c in range(6, r + 1):
            board._set_piece(r, c, 3)

def next_player(player: int) -> int:
    return 1 if player == 3 else player + 1

def get_all_moves_for_player(board: TriangleBoard, player: int) -> List[MovePath]:
    moves = []
    pieces = board.get_all_pieces(player)

    for (r, c) in pieces:
        paths = board.get_all_moves(r, c)
        moves.extend(paths)

    return moves