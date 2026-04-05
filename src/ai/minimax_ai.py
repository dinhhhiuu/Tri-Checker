from __future__ import annotations

from math import inf
from typing import Dict, List, Optional, Tuple

from src.core.board import TriangleBoard
from src.core.move import apply_move

try:
    from src.ml.model_loader import predict_winner_proba
except Exception:
    predict_winner_proba = None

MovePath = List[Tuple[int, int]]
_PLAYERS = (1, 2, 3)


def _next_player(player: int) -> int:
    return 1 if player == 3 else player + 1


def _clone_board(board: TriangleBoard) -> TriangleBoard:
    cloned = TriangleBoard(board.size)
    cloned.board = [row[:] for row in board.board]
    return cloned


def _count_captures(board: TriangleBoard, path: MovePath, player: int) -> int:
    captures = 0
    for (prev_r, prev_c), (curr_r, curr_c) in zip(path, path[1:]):
        if abs(curr_r - prev_r) == 2 or abs(curr_c - prev_c) == 2:
            mid_r = (prev_r + curr_r) // 2
            mid_c = (prev_c + curr_c) // 2
            mid_piece = board.board[mid_r][mid_c]
            if mid_piece not in (0, player):
                captures += 1
    return captures


def get_all_moves_for_player(board: TriangleBoard, player: int) -> List[MovePath]:
    moves: List[MovePath] = []
    for r in range(board.size):
        for c in range(r + 1):
            if board.board[r][c] != player:
                continue
            for path in board.get_all_moves(r, c):
                if len(path) >= 2:
                    moves.append(path)

    moves.sort(
        key=lambda path: (
            _count_captures(board, path, player),
            len(path),
            path[-1][0],
        ),
        reverse=True,
    )
    return moves


def _raw_player_score(board: TriangleBoard, player: int) -> float:
    pieces = board.get_all_pieces(player)
    piece_count = len(pieces)
    if piece_count == 0:
        return -10_000.0

    mobility = 0
    capture_pressure = 0
    advancement = 0.0

    for r, c in pieces:
        paths = board.get_all_moves(r, c)
        mobility += len(paths)
        capture_pressure += sum(_count_captures(board, path, player) for path in paths)

        if player == 1:
            advancement += r
        elif player == 2:
            advancement += (board.size - 1 - r) + c
        else:
            advancement += (board.size - 1 - r) + (r - c)

    return (
        piece_count * 100.0
        + mobility * 3.0
        + capture_pressure * 12.0
        + advancement * 0.5
    )


def _evaluate_state(
    board: TriangleBoard,
    turn: int,
    use_model: bool = True,
) -> Tuple[float, float, float]:
    winner = board.check_winner()
    if winner is not None:
        return tuple(100_000.0 if p == winner else -100_000.0 for p in _PLAYERS)

    raw_scores: Dict[int, float] = {p: _raw_player_score(board, p) for p in _PLAYERS}
    adjusted = []
    for p in _PLAYERS:
        opponents = sum(raw_scores[o] for o in _PLAYERS if o != p)
        adjusted.append(raw_scores[p] - 0.45 * opponents)

    if use_model and predict_winner_proba is not None:
        model_probs = predict_winner_proba(board, turn)
        if model_probs is not None:
            adjusted = [
                score + (probability * 250.0)
                for score, probability in zip(adjusted, model_probs)
            ]

    return tuple(adjusted)


def _candidate_moves(board: TriangleBoard, player: int, depth: int) -> List[MovePath]:
    moves = get_all_moves_for_player(board, player)
    if depth >= 3 and len(moves) > 10:
        return moves[:10]
    if depth == 2 and len(moves) > 14:
        return moves[:14]
    return moves


def _maxn(
    board: TriangleBoard,
    turn: int,
    depth: int,
    use_model: bool = True,
) -> Tuple[float, float, float]:
    if depth <= 0 or board.check_winner() is not None:
        return _evaluate_state(board, turn, use_model)

    moves = _candidate_moves(board, turn, depth)
    if not moves:
        return _maxn(board, _next_player(turn), depth - 1, use_model)

    best_value: Optional[Tuple[float, float, float]] = None
    best_turn_score = -inf

    for path in moves:
        next_board = _clone_board(board)
        apply_move(next_board, path)
        value = _maxn(next_board, _next_player(turn), depth - 1, use_model)

        turn_score = value[turn - 1]
        if best_value is None or turn_score > best_turn_score:
            best_value = value
            best_turn_score = turn_score

    return best_value if best_value is not None else _evaluate_state(board, turn, use_model)


def choose_minimax_move(
    board: TriangleBoard,
    player: int,
    mode: str,
    depth: int = 2,
    use_model: bool = True,
) -> Optional[MovePath]:
    if mode != "minimax":
        raise ValueError(f"Invalid mode for choose_minimax_move: {mode}")

    depth = max(1, min(depth, 3))
    moves = _candidate_moves(board, player, depth)
    if not moves:
        return None

    best_move: Optional[MovePath] = None
    best_score = -inf

    for path in moves:
        next_board = _clone_board(board)
        apply_move(next_board, path)
        value = _maxn(next_board, _next_player(player), depth - 1, use_model)
        score = value[player - 1]

        if best_move is None or score > best_score:
            best_move = path
            best_score = score

    return best_move
