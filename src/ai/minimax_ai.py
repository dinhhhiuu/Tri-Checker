from __future__ import annotations

from typing import List, Optional
import random
import time

from src.core.board import TriangleBoard
from src.core.move import apply_move
from src.core.utils import next_player, get_all_moves_for_player

from src.ai.utils import MovePath, clone_board, move_score

def evaluate(board: TriangleBoard, player: int) -> List[float]:
    scores = []

    for p in [1, 2, 3]:
        my_pieces = board.get_all_pieces(p)
        my_count = len(my_pieces)

        enemies = [e for e in [1,2,3] if e != p]
        enemy_count = sum(len(board.get_all_pieces(e)) for e in enemies)

        score = 0
        # piece count with higher weight
        score += my_count * 150
        score -= enemy_count * 80

        # mobility with jump bonus
        moves = 0
        jump_moves = 0
        for (r, c) in my_pieces:
            piece_moves = board.get_all_moves(r, c)
            moves += len(piece_moves)
            # Count jumps (paths longer than 2 positions)
            jump_moves += sum(1 for move in piece_moves if len(move) > 2)

        score += moves * 3
        score += jump_moves * 15  # Bonus for jump opportunities

        # Center control (lower rows are more valuable in triangular board)
        center_score = 0
        for (r, c) in my_pieces:
            # Weight pieces in lower rows more heavily
            row_weight = (r + 1) / board.size
            center_score += row_weight * 5
        score += center_score

        scores.append(score)

    return scores

def scalarize(scores: List[float], player: int) -> float:
    ''' Chuyển từ vector điểm số (cho tất cả người chơi) sang scalar score cho player hiện tại, \n
    dùng phương pháp "maximin" đơn giản: điểm của mình trừ đi điểm cao nhất của đối thủ. '''
    my_score = scores[player - 1]
    enemy_scores = [scores[i] for i in range(3) if i != player - 1]

    return my_score - max(enemy_scores)

def minimax(
    board: TriangleBoard,
    depth: int,
    current_player: int,
    root_player: int,
    alpha: float,
    beta: float
) -> float:
    ''' Hàm minimax với alpha-beta pruning, trả về điểm số ước lượng cho root_player ở node hiện tại. '''

    # Kiểm tra điều kiện dừng: nếu có người thắng
    winner = board.check_winner()
    if winner is not None:
        if winner == root_player:
            return 1e6
        else:
            return -1e6

    # Kiểm tra điều kiện dừng: nếu đạt độ sâu tối đa
    if depth == 0:
        scores = evaluate(board, root_player)
        return scalarize(scores, root_player)

    moves = get_all_moves_for_player(board, current_player)

    # Nếu không còn nước đi nào, đánh giá board ngay lập tức
    if not moves:
        scores = evaluate(board, root_player)
        return scalarize(scores, root_player)
    
    # Sort moves by heuristic score for better pruning (higher scores first for maximizing, lower for minimizing)
    if current_player == root_player:
        moves.sort(key=move_score, reverse=True)  # Better moves first for maximizing player
    else:
        moves.sort(key=move_score)  # Worse moves first for minimizing player (opponent)

    # Nếu current_player là root_player, ta muốn chọn nước đi có điểm số cao nhất (maximizing)
    if current_player == root_player:
        # value khởi đầu là -inf để tìm max
        value = float("-inf")

        for move in moves:
            new_board = clone_board(board)
            apply_move(new_board, move)

            score = minimax(
                new_board,
                depth - 1,
                next_player(current_player),
                root_player,
                alpha,
                beta
            )

            value = max(value, score)
            alpha = max(alpha, value)

            if alpha >= beta:
                break

        return value

    # Nếu current_player không phải root_player, ta giả định đối thủ sẽ chọn nước đi có điểm số thấp nhất (minimizing)
    else:
        value = float("inf")

        for move in moves:
            new_board = clone_board(board)
            apply_move(new_board, move)

            score = minimax(
                new_board,
                depth - 1,
                next_player(current_player),
                root_player,
                alpha,
                beta
            )

            value = min(value, score)
            beta = min(beta, value)

            if alpha >= beta:
                break

        return value

def choose_minimax_move(
    board: TriangleBoard,
    player: int,
    mode: str,
    depth: int = 3,
    time_limit: float = 0.5
) -> Optional[MovePath]:
    ''' Chọn nước đi tốt nhất cho player hiện tại bằng cách sử dụng thuật toán minimax với alpha-beta pruning.'''
    if mode != "minimax":
        raise ValueError(f"Invalid mode for choose_minimax_move: {mode}")
    
    moves = get_all_moves_for_player(board, player)

    if not moves:
        return None

    best_score = float("-inf")
    best_moves = []

    # Sort moves by heuristic score for better first choices
    moves.sort(key=move_score, reverse=True)

    start_time = time.time()
    
    for move in moves:
        if time.time() - start_time > time_limit:
            break  # Time limit exceeded, return best found so far
            
        new_board = clone_board(board)
        apply_move(new_board, move)

        score = minimax(
            new_board,
            depth - 1,
            next_player(player),
            player,
            float("-inf"),
            float("inf")
        )

        if score > best_score:
            best_score = score
            best_moves = [move]
        elif score == best_score:
            best_moves.append(move)

    return random.choice(best_moves) if best_moves else None