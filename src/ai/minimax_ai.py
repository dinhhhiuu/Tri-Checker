from __future__ import annotations

from typing import List, Optional, Tuple
import random
import copy

from src.core.board import TriangleBoard
from src.core.move import apply_move
from src.core.utils import next_player

MovePath = List[Tuple[int, int]]

def clone_board(board: TriangleBoard) -> TriangleBoard:
    ''' Tạo một bản sao sâu của board để tránh ảnh hưởng đến board gốc khi áp dụng move trong minimax '''
    new_board = TriangleBoard(board.size)
    new_board.board = copy.deepcopy(board.board)
    return new_board

def get_all_moves_for_player(board: TriangleBoard, player: int) -> List[MovePath]:
    ''' Lấy tất cả đường đi hợp lệ cho player hiện tại trên board '''
    moves: List[MovePath] = []

    pieces = board.get_all_pieces(player)

    for (r, c) in pieces:
        paths = board.get_all_moves(r, c)
        moves.extend(paths)

    return moves

def evaluate(board: TriangleBoard, player: int) -> float:
    scores = []

    for p in [1, 2, 3]:
        my_pieces = board.get_all_pieces(p)
        my_count = len(my_pieces) # số quân của mình trên board

        enemies = [e for e in [1,2,3] if e != p]
        enemy_count = sum(len(board.get_all_pieces(e)) for e in enemies) # tổng số quân của đối thủ trên board

        # đơn giản: mỗi quân của mình cho +100 điểm, mỗi quân đối thủ cho -60 điểm
        score = 0
        score += my_count * 100
        score -= enemy_count * 60

        # mobility: mỗi nước đi hợp lệ cho mình cho +2 điểm
        moves = 0
        for (r, c) in my_pieces:
            moves += len(board.get_all_moves(r, c))
        score += moves * 2

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
    
    random.shuffle(moves)  # giúp prune mạnh hơn

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
    depth: int = 2
) -> Optional[MovePath]:
    ''' Chọn nước đi tốt nhất cho player hiện tại bằng cách sử dụng thuật toán minimax với alpha-beta pruning.'''
    if mode != "minimax":
        raise ValueError(f"Invalid mode for choose_minimax_move: {mode}")
    
    moves = get_all_moves_for_player(board, player)

    if not moves:
        return None

    best_score = float("-inf")
    best_moves = []

    random.shuffle(moves)

    for move in moves:
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