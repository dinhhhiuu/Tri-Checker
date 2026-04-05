from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from src.core.board import TriangleBoard
from src.core.move import apply_move

try:
    from src.ml.model_loader import predict_winner_proba
except Exception:
    predict_winner_proba = None

MovePath = List[Tuple[int, int]]


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


def _progress_gain(board: TriangleBoard, path: MovePath, player: int) -> float:
    (start_r, start_c), (end_r, end_c) = path[0], path[-1]

    def progress_value(row: int, col: int) -> float:
        if player == 1:
            return float(row)
        if player == 2:
            return float((board.size - 1 - row) + col)
        return float((board.size - 1 - row) + (row - col))

    return progress_value(end_r, end_c) - progress_value(start_r, start_c)


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
            _progress_gain(board, path, player),
            len(path),
            path[-1][0],
        ),
        reverse=True,
    )
    return moves


def _leader_after_cutoff(board: TriangleBoard) -> Optional[int]:
    piece_counts = {player: len(board.get_all_pieces(player)) for player in (1, 2, 3)}
    best_player = max(piece_counts, key=piece_counts.get)
    if piece_counts[best_player] == 0:
        return None

    if list(piece_counts.values()).count(piece_counts[best_player]) == 1:
        return best_player

    mobility = {player: len(get_all_moves_for_player(board, player)) for player in (1, 2, 3)}
    return max(mobility, key=mobility.get)


def _estimate_reward(
    board: TriangleBoard,
    turn: int,
    root_player: int,
    use_ml: bool = True,
) -> float:
    winner = board.check_winner()
    if winner is not None:
        return 1.0 if winner == root_player else 0.0

    if use_ml and predict_winner_proba is not None:
        probs = predict_winner_proba(board, turn)
        if probs is not None:
            return float(probs[root_player - 1])

    leader = _leader_after_cutoff(board)
    if leader is None:
        return 0.33
    return 1.0 if leader == root_player else 0.0


def _select_rollout_move(board: TriangleBoard, turn: int, moves: List[MovePath]) -> MovePath:
    top_moves = moves[: min(len(moves), 6)]
    if len(top_moves) == 1:
        return top_moves[0]

    weights = []
    for path in top_moves:
        score = (
            1.0
            + (_count_captures(board, path, turn) * 4.0)
            + max(_progress_gain(board, path, turn), 0.0)
            + (len(path) * 0.5)
        )
        weights.append(max(score, 0.1))

    return random.choices(top_moves, weights=weights, k=1)[0]


def _rollout(
    board: TriangleBoard,
    turn: int,
    root_player: int,
    max_steps: int = 32,
    use_ml: bool = True,
) -> float:
    consecutive_passes = 0

    for step in range(max_steps):
        winner = board.check_winner()
        if winner is not None:
            return 1.0 if winner == root_player else 0.0

        moves = get_all_moves_for_player(board, turn)
        if not moves:
            consecutive_passes += 1
            if consecutive_passes >= 3:
                break
            turn = _next_player(turn)
            continue

        consecutive_passes = 0
        move = _select_rollout_move(board, turn, moves)
        apply_move(board, move)
        turn = _next_player(turn)

    return _estimate_reward(board, turn, root_player, use_ml)


@dataclass
class _Node:
    board: TriangleBoard
    turn: int
    root_player: int
    move: Optional[MovePath] = None
    parent: Optional["_Node"] = None
    children: List["_Node"] = field(default_factory=list)
    untried_moves: List[MovePath] = field(default_factory=list)
    visits: int = 0
    wins: float = 0.0
    prior: float = 0.0
    use_ml: bool = True

    def __post_init__(self) -> None:
        if not self.untried_moves:
            self.untried_moves = get_all_moves_for_player(self.board, self.turn)

    def is_terminal(self) -> bool:
        return self.board.check_winner() is not None

    def is_fully_expanded(self) -> bool:
        return len(self.untried_moves) == 0

    def best_child(self, exploration_weight: float = math.sqrt(2.0)) -> "_Node":
        def ucb_score(child: "_Node") -> float:
            if child.visits == 0:
                return float("inf")
            exploit = child.wins / child.visits
            explore = exploration_weight * math.sqrt(math.log(max(self.visits, 1)) / child.visits)
            bias = 0.35 * child.prior / (1 + child.visits)
            return exploit + explore + bias

        return max(self.children, key=ucb_score)

    def expand(self) -> "_Node":
        move = self.untried_moves.pop(0)
        next_board = _clone_board(self.board)
        apply_move(next_board, move)
        child = _Node(
            board=next_board,
            turn=_next_player(self.turn),
            root_player=self.root_player,
            move=move,
            parent=self,
            prior=_estimate_reward(next_board, _next_player(self.turn), self.root_player, self.use_ml),
            use_ml=self.use_ml,
        )
        self.children.append(child)
        return child

    def update(self, reward: float) -> None:
        self.visits += 1
        self.wins += reward


def choose_mcts_move(
    board: TriangleBoard,
    player: int,
    mode: str,
    simulations: int = 200,
    use_ml: bool = True,
) -> Optional[MovePath]:
    if mode != "mcts":
        raise ValueError(f"Invalid mode for choose_mcts_move: {mode}")

    root = _Node(board=_clone_board(board), turn=player, root_player=player, use_ml=use_ml)
    if not root.untried_moves:
        return None

    simulations = max(1, min(simulations, 1000))

    for _ in range(simulations):
        node = root

        while not node.is_terminal() and node.is_fully_expanded() and node.children:
            node = node.best_child()

        if not node.is_terminal() and node.untried_moves:
            node = node.expand()

        rollout_board = _clone_board(node.board)
        reward = _rollout(rollout_board, node.turn, node.root_player, use_ml=node.use_ml)

        while node is not None:
            node.update(reward)
            node = node.parent

    if not root.children:
        return random.choice(root.untried_moves)

    best_child = max(
        root.children,
        key=lambda child: (
            child.wins / child.visits if child.visits else 0.0,
            child.visits,
            child.prior,
        ),
    )
    return best_child.move