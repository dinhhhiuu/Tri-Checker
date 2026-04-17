from src.core.board import TriangleBoard
from typing import List, Tuple

MovePath = List[Tuple[int, int]]

def init_players(board: TriangleBoard, active_players: List[int] | Tuple[int, ...] = (1, 2, 3)) -> None:
    players = set(active_players)

    # Player 1 (top)
    if 1 in players:
        for r in range(4):
            for c in range(r + 1):
                board._set_piece(r, c, 1)

    # Player 2 (bottom-left)
    if 2 in players:
        for r in range(6, 10):
            for c in range(0, r - 5):
                board._set_piece(r, c, 2)

    # Player 3 (bottom-right)
    if 3 in players:
        for r in range(6, 10):
            for c in range(6, r + 1):
                board._set_piece(r, c, 3)

def next_player(player: int, active_players: List[int] | Tuple[int, ...] = (1, 2, 3)) -> int:
    rotation = list(active_players)

    if not rotation:
        raise ValueError("active_players must not be empty")

    if player not in rotation:
        return rotation[0]

    idx = rotation.index(player)
    return rotation[(idx + 1) % len(rotation)]

def get_all_moves_for_player(board: TriangleBoard, player: int) -> List[MovePath]:
    moves = []
    pieces = board.get_all_pieces(player)

    for (r, c) in pieces:
        paths = board.get_all_moves(r, c)
        moves.extend(paths)

    return moves

def is_valid_move_for_player(board: TriangleBoard, player: int, path: MovePath) -> bool:
    if not path:
        return False

    start_row, start_col = path[0]
    if board.board[start_row][start_col] != player:
        return False

    legal_moves = board.get_all_moves(start_row, start_col)
    return path in legal_moves