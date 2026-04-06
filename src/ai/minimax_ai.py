from __future__ import annotations

from typing import List, Optional
import random

from src.core.board import TriangleBoard
from src.core.move import apply_move
from src.core.utils import next_player, get_all_moves_for_player

from src.ai.utils import MovePath, clone_board

def evaluate(board: TriangleBoard, player: int) -> float:
    scores = []

    for p in [1, 2, 3]:
        my_pieces = board.get_all_pieces(p)
        my_count = len(my_pieces) # number of my pieces on the board

        enemies = [e for e in [1,2,3] if e != p]
        enemy_count = sum(len(board.get_all_pieces(e)) for e in enemies) # total number of opponent pieces on the board

        # simple: each of my pieces gives +100 points, each opponent piece gives -60 points
        score = 0
        score += my_count * 100
        score -= enemy_count * 60

        # mobility: each valid move for me gives +2 points
        moves = 0
        for (r, c) in my_pieces:
            moves += len(board.get_all_moves(r, c))
        score += moves * 2

        scores.append(score)

    return scores

def scalarize(scores: List[float], player: int) -> float:
    ''' Convert the score vector (for all players) to the current player's scalar score using the \n
    simple "maximin" method: subtract your opponent's highest score from your own score. '''
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
    ''' 
        The minimax function with alpha-beta pruning returns an 
        estimated score for root_player at the current node. 
    '''

    # Check the stopping conditions: if there is a winner
    winner = board.check_winner()
    if winner is not None:
        if winner == root_player:
            return 1e6
        else:
            return -1e6

    # Check the stopping condition: if the maximum depth is reached.
    if depth == 0:
        scores = evaluate(board, root_player)
        return scalarize(scores, root_player)

    moves = get_all_moves_for_player(board, current_player)

    # If there are no more moves, evaluate the board immediately.
    if not moves:
        scores = evaluate(board, root_player)
        return scalarize(scores, root_player)
    
    random.shuffle(moves)  # make the prune stronger

    # If current_player is root_player, we want to select the move with the highest score (maximizing).
    if current_player == root_player:
        # The starting value is -inf to find the maximum.
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

    # If current_player is not root_player, we assume the opponent will choose the move with the lowest score (minimizing)
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
    ''' 
        Choose the best move for the current player using 
        the minimax algorithm with alpha-beta pruning.
    '''
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