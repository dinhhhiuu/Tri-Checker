from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from src.ai.mcts_ai import choose_mcts_move
from src.ai.minimax_ai import choose_minimax_move
from src.core.board import TriangleBoard
from src.core.move import apply_move
from src.ml.model_loader import board_to_features

PLAYERS = (1, 2, 3)
STRATEGIES = ("random", "minimax", "mcts")


def init_players(board: TriangleBoard) -> None:
    for r in range(4):
        for c in range(r + 1):
            board._set_piece(r, c, 1)

    for r in range(6, 10):
        for c in range(0, r - 5):
            board._set_piece(r, c, 2)

    for r in range(6, 10):
        for c in range(6, r + 1):
            board._set_piece(r, c, 3)


def next_player(player: int) -> int:
    return 1 if player == 3 else player + 1


def _all_moves_for_player(board: TriangleBoard, player: int):
    moves = []
    for r, c in board.get_all_pieces(player):
        for path in board.get_all_moves(r, c):
            if len(path) >= 2:
                moves.append(path)
    return moves


def _move_capture_count(board: TriangleBoard, path, player: int) -> int:
    captures = 0
    for (prev_r, prev_c), (curr_r, curr_c) in zip(path, path[1:]):
        if abs(curr_r - prev_r) == 2 or abs(curr_c - prev_c) == 2:
            mid_r = (prev_r + curr_r) // 2
            mid_c = (prev_c + curr_c) // 2
            mid_piece = board.board[mid_r][mid_c]
            if mid_piece not in (0, player):
                captures += 1
    return captures


def _progress_score(board: TriangleBoard, path, player: int) -> float:
    (start_r, start_c), (end_r, end_c) = path[0], path[-1]

    def progress_value(row: int, col: int) -> float:
        if player == 1:
            return float(row)
        if player == 2:
            return float((board.size - 1 - row) + col)
        return float((board.size - 1 - row) + (row - col))

    return progress_value(end_r, end_c) - progress_value(start_r, start_c)


def _score_move(board: TriangleBoard, path, player: int) -> float:
    return (
        (_move_capture_count(board, path, player) * 8.0)
        + (max(_progress_score(board, path, player), 0.0) * 1.5)
        + len(path)
    )


def _pick_weighted_top_move(board: TriangleBoard, player: int):
    moves = _all_moves_for_player(board, player)
    if not moves:
        return None

    moves.sort(key=lambda path: _score_move(board, path, player), reverse=True)
    top_moves = moves[: min(len(moves), 8)]
    weights = [max(0.1, _score_move(board, path, player)) for path in top_moves]
    return random.choices(top_moves, weights=weights, k=1)[0]


def _choose_move(board: TriangleBoard, player: int, strategy: str, turn_index: int):
    if strategy == "random":
        return _pick_weighted_top_move(board, player)

    if strategy == "minimax":
        depth = 2 if turn_index >= 4 or random.random() < 0.75 else 1
        return choose_minimax_move(board, player, mode="minimax", depth=depth, use_model=False)

    if strategy == "mcts":
        simulations = 32 if turn_index < 6 else 48
        if turn_index >= 12:
            simulations += 16
        return choose_mcts_move(board, player, mode="mcts", simulations=simulations, use_ml=False)

    raise ValueError(f"Unsupported strategy: {strategy}")


def _sample_strategy_map(game_index: int) -> Dict[int, str]:
    presets = [
        {1: "minimax", 2: "mcts", 3: "random"},
        {1: "mcts", 2: "minimax", 3: "random"},
        {1: "minimax", 2: "random", 3: "mcts"},
        {1: "random", 2: "minimax", 3: "mcts"},
        {1: "mcts", 2: "random", 3: "minimax"},
        {1: "random", 2: "mcts", 3: "minimax"},
    ]
    mapping = presets[game_index % len(presets)].copy()

    for player in PLAYERS:
        if random.random() < 0.15:
            mapping[player] = random.choice(STRATEGIES)
    return mapping


def _diverse_opening(board: TriangleBoard, turn: int, steps: int) -> int:
    opening_plan = ("random", "random", "minimax", "random", "mcts")
    for idx in range(steps):
        strategy = opening_plan[idx % len(opening_plan)]
        move = _choose_move(board, turn, strategy=strategy, turn_index=idx)
        if move:
            apply_move(board, move)
        turn = next_player(turn)
    return turn


def _fallback_winner(board: TriangleBoard) -> int:
    piece_counts = {player: len(board.get_all_pieces(player)) for player in PLAYERS}
    best_count = max(piece_counts.values())
    leaders = [player for player, count in piece_counts.items() if count == best_count]
    if len(leaders) == 1:
        return leaders[0]

    mobility = {
        player: sum(len(board.get_all_moves(r, c)) for r, c in board.get_all_pieces(player))
        for player in leaders
    }
    return max(mobility, key=mobility.get)


def _state_repeat_factor(
    board: TriangleBoard,
    turn_index: int,
    max_turns: int,
    capture_count: int = 0,
) -> int:
    remaining_pieces = sum(len(board.get_all_pieces(player)) for player in PLAYERS)
    progress = (turn_index + 1) / max(max_turns, 1)

    repeats = 1
    if progress >= 0.45:
        repeats += 1
    if progress >= 0.75 or remaining_pieces <= 20:
        repeats += 1
    if capture_count > 0:
        repeats += min(capture_count, 2)

    return min(repeats, 4)


def simulate_game(
    max_turns: int = 80,
    strategies: Optional[Dict[int, str]] = None,
) -> Tuple[List[List[float]], int]:
    board = TriangleBoard()
    init_players(board)

    turn = _diverse_opening(board, turn=1, steps=random.randint(1, 6))
    strategies = strategies or _sample_strategy_map(0)
    states: List[List[float]] = []
    consecutive_passes = 0

    for turn_index in range(max_turns):
        winner = board.check_winner()
        if winner is not None:
            return states, winner

        snapshot = board_to_features(board, turn)
        pre_repeats = _state_repeat_factor(board, turn_index, max_turns)
        states.extend([snapshot[:] for _ in range(pre_repeats)])

        move = _choose_move(board, turn, strategies[turn], turn_index)

        if move is None:
            consecutive_passes += 1
            if consecutive_passes >= len(PLAYERS):
                break
            turn = next_player(turn)
            continue

        capture_count = _move_capture_count(board, move, turn)
        consecutive_passes = 0
        apply_move(board, move)
        turn = next_player(turn)

        if capture_count > 0 or turn_index >= max_turns // 2:
            post_snapshot = board_to_features(board, turn)
            post_repeats = _state_repeat_factor(board, turn_index, max_turns, capture_count)
            states.extend([post_snapshot[:] for _ in range(post_repeats)])

    return states, _fallback_winner(board)


def generate_dataset(
    games: int,
    max_turns: int,
    seed: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    all_states: List[List[float]] = []
    labels: List[int] = []
    winner_counts = {player: 0 for player in PLAYERS}

    max_games = max(games, 3) + 12
    game_index = 0
    while game_index < games or any(count == 0 for count in winner_counts.values()):
        if game_index >= max_games:
            print(f"Stopping after {max_games} games; winner coverage so far: {winner_counts}")
            break

        strategies = _sample_strategy_map(game_index)
        states, winner = simulate_game(max_turns=max_turns, strategies=strategies)
        all_states.extend(states)
        labels.extend([winner] * len(states))
        winner_counts[winner] += 1
        print(
            f"Game {game_index + 1}: winner=P{winner}, "
            f"states={len(states)}, strategies={strategies}, winner_counts={winner_counts}"
        )
        game_index += 1

    X = np.asarray(all_states, dtype=float)
    y = np.asarray(labels, dtype=int)
    return X, y


def save_dataset(output_path: Path, X: np.ndarray, y: np.ndarray) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output_path, X=X, y=y)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate self-play data for Triangle Board ML.")
    parser.add_argument("--games", type=int, default=24, help="Number of self-play games to simulate.")
    parser.add_argument("--max-turns", type=int, default=80, help="Maximum turns per game.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data") / "self_play_data.npz",
        help="Where to save the generated dataset.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    X, y = generate_dataset(games=args.games, max_turns=args.max_turns, seed=args.seed)

    if len(X) == 0:
        raise RuntimeError("No training samples were generated.")

    save_dataset(args.output, X, y)
    print(f"Saved dataset to {args.output} with shape X={X.shape}, y={y.shape}")


if __name__ == "__main__":
    main()
