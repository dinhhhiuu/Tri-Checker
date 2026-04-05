from __future__ import annotations

import argparse
import json
import os
import random
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional, Sequence, Tuple

from src.core.board import TriangleBoard
from src.core.move import apply_move
from src.core.utils import next_player, get_all_moves_for_player

from src.ai.random_ai import choose_random_move
from src.ai.minimax_ai import choose_minimax_move
from src.ai.mcts_ai import choose_mcts_move
from src.ai.ml_ai import choose_ml_move

Mode = Literal["player", "random", "minimax", "mcts", "ml"]
MovePath = List[Tuple[int, int]]


@dataclass
class StepRecord:
    game_id: int # id ván game
    step: int # bước thức mấy trong ván game này
    board: List[List[int]] # trạng thái bàn cờ trước khi đi
    turn: int # người chơi nào đang đi (1, 2, 3)
    move: List[Tuple[int, int]] # đường đi đã chọn
    advantage_player: int # ai đánh giá người có lợi thế nhất ở trạng thái này (0 nếu hòa)
    advantage_scores: Dict[int, float] # điểm đánh giá lợi thế cho mỗi người chơi (càng cao càng có lợi thế)

    def to_json(self) -> str:
        '''Convert record to JSON string.'''
        payload = {
            "game_id": self.game_id,
            "step": self.step,
            "board": self.board,
            "turn": self.turn,
            "move": [[r, c] for (r, c) in self.move],
            "advantage_player": self.advantage_player,
            "advantage_scores": {str(k): v for k, v in self.advantage_scores.items()},
        }
        return json.dumps(payload, ensure_ascii=False)


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


def copy_board(board: TriangleBoard) -> List[List[int]]:
    '''Return a deep copy of the board state as a list of lists.'''
    return [row[:] for row in board.board]


def mobility(board: TriangleBoard, player: int) -> int:
    '''Count the total number of valid moves for player on the current board.'''
    count = 0
    for r, c in board.get_all_pieces(player):
        count += len(board.get_all_moves(r, c))
    return count


def advantage(board: TriangleBoard, *, tie_epsilon: float = 1e-6) -> Tuple[int, Dict[int, float]]:
    """
        Return (advantage_player, scores).
        Heuristic (fast, deterministic): piece_count heavily weighted + mobility.
        - advantage_player: 1, 2, or 3 for the player with the highest score; 0 if tie.
        - scores: dict mapping player number to their score (higher is better).
    """
    scores: Dict[int, float] = {}
    for p in (1, 2, 3):
        piece_count = len(board.get_all_pieces(p))
        move_count = mobility(board, p)
        scores[p] = piece_count * 100.0 + move_count * 2.0

    # winner should dominate advantage
    w = board.check_winner()
    if w is not None:
        for p in (1, 2, 3):
            scores[p] = 1e9 if p == w else -1e9
        return w, scores

    best_p = max(scores, key=scores.get)
    sorted_scores = sorted(scores.values(), reverse=True)
    if len(sorted_scores) >= 2 and abs(sorted_scores[0] - sorted_scores[1]) <= tie_epsilon:
        return 0, scores
    return best_p, scores


def choose_move(board: TriangleBoard, player: int, mode: Mode, rng: random.Random) -> Optional[MovePath]:
    '''Choose a move for the given player and mode. Returns None if no moves available.'''
    if mode == "player":
        mode = "random"

    if mode == "random":
        return choose_random_move(board, player, mode="random")

    if mode == "minimax":
        return choose_minimax_move(board, player, mode="minimax", depth=2)

    if mode == "mcts":
        return choose_mcts_move(board, player, mode="mcts", simulations=100)

    if mode == "ml":
        return choose_ml_move(board, player, mode="ml")

    # Fallback (shouldn't happen)
    moves = get_all_moves_for_player(board, player)
    return rng.choice(moves) if moves else None


def play_one_game(
    *,
    game_id: int,
    rng: random.Random,
    max_steps: int,
    player_modes: Dict[int, Mode], # mapping player number to their mode (1 -> random, 2 -> minimax, etc.)
) -> List[StepRecord]:
    '''Play one game and return the list of StepRecords.'''
    
    # init board and players
    board = TriangleBoard()
    init_players(board)
    turn = 1
    records: List[StepRecord] = []

    for step in range(max_steps):
        if board.check_winner() is not None:
            break

        mode = player_modes.get(turn, "random")
        move = choose_move(board, turn, mode, rng)
        if not move:
            break

        adv_p, adv_scores = advantage(board)
        records.append(
            StepRecord(
                game_id=game_id,
                step=step,
                board=copy_board(board),
                turn=turn,
                move=move,
                advantage_player=adv_p,
                advantage_scores=adv_scores,
            )
        )

        apply_move(board, move)
        turn = next_player(turn)

    return records


def ensure_parent_dir(path: str) -> None:
    '''Ensure the parent directory of the given path exists.'''
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def _read_last_nonempty_line(path: str) -> Optional[str]:
    """Read the last non-empty line from a potentially large file to determine the last game_id.
    Returns None if the file doesn't exist or is empty."""
    if not os.path.exists(path):
        return None

    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            end = f.tell()
            if end == 0:
                return None

            block_size = 8192
            pos = end
            buf = b""

            while pos > 0 and b"\n" not in buf:
                read_size = block_size if pos >= block_size else pos
                pos -= read_size
                f.seek(pos)
                buf = f.read(read_size) + buf
                if len(buf) > 256_000:
                    break

            lines = buf.splitlines()
            for raw in reversed(lines):
                if raw.strip():
                    return raw.decode("utf-8", errors="ignore")
    except OSError:
        return None

    return None


def get_next_game_id(out_path: str) -> int:
    """Return next game_id for appending (JSONL only).

    - If file doesn't exist / empty -> 0
    - Else -> last_game_id + 1
    """
    last_line = _read_last_nonempty_line(out_path)
    if not last_line:
        return 0

    try:
        obj = json.loads(last_line)
        last_id = int(obj.get("game_id", -1))
        return max(0, last_id + 1)

    except Exception:
        return 0


def write_jsonl(out_path: str, records: Sequence[StepRecord]) -> None:
    ensure_parent_dir(out_path)
    with open(out_path, "a", encoding="utf-8") as f:
        for rec in records:
            f.write(rec.to_json() + "\n")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Self-play data generator for TriangleBoard")
    parser.add_argument("--games", type=int, default=10, help="Number of self-play games")
    parser.add_argument("--max-steps", type=int, default=300, help="Max steps per game")
    parser.add_argument(
        "--out",
        type=str,
        default=os.path.join("data", "ml_dataset.jsonl"),
        help="Output JSONL file",
    )
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--p1", choices=("player", "random", "minimax", "mcts", "ml"), default="random")
    parser.add_argument("--p2", choices=("player", "random", "minimax", "mcts", "ml"), default="random")
    parser.add_argument("--p3", choices=("player", "random", "minimax", "mcts", "ml"), default="random")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    # Seed both a local RNG and the global random module so imported AI modules
    # (minimax/mcts/random) behave deterministically for a given --seed.
    random.seed(args.seed)
    rng = random.Random(args.seed)

    player_modes: Dict[int, Mode] = {1: args.p1, 2: args.p2, 3: args.p3}
    total_steps = 0

    base_game_id = get_next_game_id(args.out)

    for i in range(args.games):
        gid = base_game_id + i
        records = play_one_game(
            game_id=gid,
            rng=rng,
            max_steps=args.max_steps,
            player_modes=player_modes,
        )
        total_steps += len(records)
        write_jsonl(args.out, records)

    print(f"Wrote {total_steps} steps to {args.out}")


if __name__ == "__main__":
    main()